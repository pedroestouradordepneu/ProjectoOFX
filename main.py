"""ProjetoOFX: leitura de extrato, relatório financeiro e integração PostgreSQL.

Executar:
    python main.py
    python main.py --salvar resultado_extrato.txt
    python main.py --postgres
    python main.py --csv movimentacoes.csv
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from leitor_ofx import ler_ofx

PASTA_PROJETO = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Movimentacao:
    data: date
    valor: Decimal
    descricao: str
    chave_unica: str


def importar_movimentacoes(caminho: str | Path) -> list[Movimentacao]:
    """Extrai, transforma e identifica movimentações do extrato OFX."""
    ofx = ler_ofx(caminho)
    conta = getattr(ofx, "account", None)
    if conta is None or getattr(conta, "statement", None) is None:
        raise ValueError("Não foi encontrada uma conta com extrato bancário no OFX.")

    referencia_conta = "|".join([
        str(getattr(conta, "routing_number", "") or ""),
        str(getattr(conta, "branch_id", "") or ""),
        str(getattr(conta, "account_id", "") or ""),
    ])
    ocorrencias_sem_fitid: Counter[str] = Counter()
    movimentacoes = []

    for transacao in conta.statement.transactions:
        data_original = transacao.date
        if isinstance(data_original, datetime):
            data_movimentacao = data_original.date()
        elif isinstance(data_original, date):
            data_movimentacao = data_original
        else:
            raise ValueError("Transação sem data válida.")

        valor = Decimal(str(transacao.amount)).quantize(Decimal("0.01"))
        descricao = (getattr(transacao, "memo", None) or
                     getattr(transacao, "payee", None) or "Sem descrição").strip()
        identificador = str(getattr(transacao, "id", "") or "").strip()

        if identificador:
            base_identidade = f"{referencia_conta}|FITID|{identificador}"
        else:
            # Alternativa quando o banco não informa FITID: distingue operações
            # idênticas dentro de um mesmo extrato e evita reinserção do arquivo.
            assinatura = f"{data_movimentacao}|{valor}|{descricao}"
            ocorrencias_sem_fitid[assinatura] += 1
            base_identidade = (
                f"{referencia_conta}|SEM_FITID|{assinatura}|"
                f"{ocorrencias_sem_fitid[assinatura]}"
            )

        chave = hashlib.sha256(base_identidade.encode("utf-8")).hexdigest()
        movimentacoes.append(Movimentacao(
            data=data_movimentacao,
            valor=valor,
            descricao=descricao,
            chave_unica=chave,
        ))

    return movimentacoes


def calcular_totais(movimentacoes: list[Movimentacao]) -> tuple[Decimal, Decimal, Decimal]:
    entradas = sum((m.valor for m in movimentacoes if m.valor > 0), Decimal("0.00"))
    saidas = sum((m.valor for m in movimentacoes if m.valor < 0), Decimal("0.00"))
    return entradas, saidas, entradas + saidas


def moeda(valor: Decimal) -> str:
    """Formata valores como R$ 1.234,56 ou R$ -1.234,56."""
    sinal = "-" if valor < 0 else ""
    numero = f"{abs(valor):,.2f}".replace(",", "§").replace(".", ",").replace("§", ".")
    return f"R$ {sinal}{numero}"


def gerar_relatorio(movimentacoes: list[Movimentacao]) -> str:
    linhas = ["=" * 62, "                    EXTRATO BANCÁRIO", "=" * 62, ""]
    for posicao, mov in enumerate(movimentacoes, 1):
        linhas.extend([
            f"Movimentação {posicao:02d}",
            f"Data      : {mov.data:%d/%m/%Y}",
            f"Valor     : {moeda(mov.valor)}",
            f"Descrição : {mov.descricao}",
            "-" * 62,
        ])
    entradas, saidas, saldo = calcular_totais(movimentacoes)
    linhas.extend([
        "", "RESUMO FINANCEIRO", "=" * 62,
        f"Quantidade total de movimentações: {len(movimentacoes)}",
        f"Total de entradas               : {moeda(entradas)}",
        f"Total de saídas                 : {moeda(saidas)}",
        f"Saldo calculado                 : {moeda(saldo)}",
        "", "Observação: saldo calculado = entradas + saídas do período;",
        "pode ser diferente do saldo final informado pelo banco.",
    ])
    return "\n".join(linhas) + "\n"


def exportar_csv(movimentacoes: list[Movimentacao], caminho: str | Path) -> None:
    """Exportação extra, compatível com planilhas configuradas para pt-BR."""
    with Path(caminho).open("w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.writer(arquivo, delimiter=";")
        escritor.writerow(["Data", "Valor", "Descrição"])
        for mov in movimentacoes:
            escritor.writerow([
                mov.data.strftime("%d/%m/%Y"),
                f"{mov.valor:.2f}".replace(".", ","),
                mov.descricao,
            ])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Leitura de arquivo OFX e resumo financeiro com PostgreSQL opcional."
    )
    parser.add_argument(
        "--arquivo", type=Path, default=PASTA_PROJETO / "extrato.ofx",
        help="Caminho do OFX; padrão: extrato.ofx na pasta do projeto",
    )
    parser.add_argument(
        "--postgres", action="store_true",
        help="Grava as transações no PostgreSQL, ignorando duplicadas",
    )
    parser.add_argument(
        "--salvar", type=Path,
        help="Salva uma cópia do relatório em TXT",
    )
    parser.add_argument("--csv", type=Path, help="Exporta as transações para CSV")
    argumentos = parser.parse_args(argv)

    try:
        movimentacoes = importar_movimentacoes(argumentos.arquivo)
        relatorio = gerar_relatorio(movimentacoes)
        print(relatorio, end="")

        if argumentos.salvar:
            argumentos.salvar.write_text(relatorio, encoding="utf-8")
            print(f"\nRelatório salvo em: {argumentos.salvar}")
        if argumentos.csv:
            exportar_csv(movimentacoes, argumentos.csv)
            print(f"CSV exportado para: {argumentos.csv}")

        if argumentos.postgres:
            from banco import gravar_movimentacoes
            inseridas, ignoradas = gravar_movimentacoes(movimentacoes)
            print("\nINTEGRAÇÃO POSTGRESQL")
            print(f"Registros inseridos : {inseridas}")
            print(f"Duplicatas ignoradas: {ignoradas}")
        return 0
    except (OSError, ValueError, ImportError, ArithmeticError) as erro:
        print(f"ERRO: {erro}", file=sys.stderr)
        return 1
    except Exception as erro:
        # Banco de dados pode retornar exceções específicas de conexão/SQL.
        print(f"ERRO ao processar o extrato: {erro}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
