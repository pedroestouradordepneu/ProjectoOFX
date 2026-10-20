

from __future__ import annotations

import re
import sys
from datetime import datetime
from decimal import Decimal
from html import unescape
from pathlib import Path
from types import SimpleNamespace

def _campo(bloco: str, nome: str) -> str:
    encontrado = re.search(rf"<{re.escape(nome)}\s*>\s*([^\r\n<]*)", bloco, re.I)
    return unescape(encontrado.group(1).strip()) if encontrado else ""

def _ler_sem_biblioteca(caminho: Path):

    dados = caminho.read_bytes()
    try:
        texto = dados.decode("utf-8-sig")
    except UnicodeDecodeError:
        texto = dados.decode("cp1252")

    if not re.search(r"<OFX(?:\s|>)", texto, re.I):
        raise ValueError("O arquivo não contém a estrutura OFX esperada.")
    if not re.search(r"<BANKTRANLIST(?:\s|>)", texto, re.I):
        raise ValueError("Arquivo sem lista de movimentações bancárias (BANKTRANLIST).")

    transacoes = []
    blocos = re.findall(r"<STMTTRN\s*>(.*?)</STMTTRN\s*>", texto, re.I | re.S)
    for indice, bloco in enumerate(blocos, 1):
        data_bruta = _campo(bloco, "DTPOSTED")
        valor_bruto = _campo(bloco, "TRNAMT")
        if len(data_bruta) < 8 or not valor_bruto:
            raise ValueError(f"Transação {indice} sem data ou valor.")
        try:
            data = datetime.strptime(data_bruta[:8], "%Y%m%d")
            valor = Decimal(valor_bruto.replace(",", "."))
        except (ValueError, ArithmeticError) as erro:
            raise ValueError(f"Dados inválidos na transação {indice}.") from erro
        transacoes.append(SimpleNamespace(
            date=data,
            amount=valor,
            memo=_campo(bloco, "MEMO"),
            payee=_campo(bloco, "NAME"),
            id=_campo(bloco, "FITID"),
        ))

    conta = SimpleNamespace(
        account_id=_campo(texto, "ACCTID"),
        routing_number=_campo(texto, "BANKID"),
        branch_id=_campo(texto, "BRANCHID"),
        statement=SimpleNamespace(transactions=transacoes),
    )
    return SimpleNamespace(account=conta)

def ler_ofx(caminho: str | Path):

    caminho = Path(caminho)
    if not caminho.is_file():
        raise FileNotFoundError(f"Arquivo OFX não encontrado: {caminho}")

    with caminho.open("rb") as arquivo:
        cabecalho = arquivo.read(4096).upper()
    if b"<OFX" not in cabecalho:
        raise ValueError("O arquivo não contém a estrutura OFX esperada.")
    try:
        from ofxparse import OfxParser
    except ImportError:
        print(
            "Aviso: ofxparse indisponível; utilizando leitor básico de OFX bancário. "
            "Para leitura completa, instale: pip install -r requirements.txt",
            file=sys.stderr,
        )
        return _ler_sem_biblioteca(caminho)

    with caminho.open("rb") as arquivo:
        return OfxParser.parse(arquivo)
