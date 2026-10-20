

import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from leitor_ofx import _ler_sem_biblioteca

from banco import gravar_movimentacoes
from main import (
    Movimentacao,
    calcular_totais,
    exportar_csv,
    gerar_relatorio,
    importar_movimentacoes,
    main,
    moeda,
)

PASTA = Path(__file__).resolve().parents[1]

class CursorFalso:
    def __init__(self, banco):
        self.banco = banco
        self.ultimo_id = None
        self.insercoes = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute(self, sql, parametros=None):
        if parametros is None:
            assert "CREATE TABLE" in sql
            return
        self.insercoes += 1
        chave = parametros[3]
        if chave in self.banco:
            self.ultimo_id = None
        else:
            self.banco.add(chave)
            self.ultimo_id = len(self.banco)

    def fetchone(self):
        return (self.ultimo_id,) if self.ultimo_id is not None else None

class ConexaoFalsa:
    def __init__(self):
        self.banco = set()
        self.cursor_falso = CursorFalso(self.banco)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def cursor(self):
        return self.cursor_falso

class ProjetoOFXTestes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.extrato = importar_movimentacoes(PASTA / "extrato.ofx")

    def test_quantidade_movimentacoes(self):
        self.assertEqual(len(self.extrato), 15)

    def test_totais_extrato_fornecido(self):
        self.assertEqual(calcular_totais(self.extrato), (
            Decimal("17900.00"), Decimal("-6059.70"), Decimal("11840.30")
        ))

    def test_estrutura_campos(self):
        primeira = self.extrato[0]
        self.assertEqual(primeira.data, date(2026, 10, 1))
        self.assertEqual(primeira.valor, Decimal("4500.00"))
        self.assertIn("RECEBIMENTO", primeira.descricao)
        self.assertEqual(len(primeira.chave_unica), 64)

    def test_chave_consistente_entre_importacoes(self):
        importadas_novamente = importar_movimentacoes(PASTA / "extrato.ofx")
        self.assertEqual(
            [m.chave_unica for m in self.extrato],
            [m.chave_unica for m in importadas_novamente],
        )
        self.assertEqual(len({m.chave_unica for m in self.extrato}), 15)

    def test_reimportacao_ignora_duplicatas_postgres(self):
        conexao = ConexaoFalsa()
        self.assertEqual(gravar_movimentacoes(self.extrato, conexao), (15, 0))
        self.assertEqual(gravar_movimentacoes(self.extrato, conexao), (0, 15))
        self.assertEqual(len(conexao.banco), 15)

    def test_relatorio_exibe_resumo(self):
        texto = gerar_relatorio(self.extrato)
        self.assertIn("Quantidade total de movimentações: 15", texto)
        self.assertIn("R$ 17.900,00", texto)
        self.assertIn("R$ -6.059,70", texto)
        self.assertIn("R$ 11.840,30", texto)

    def test_formatacao_valores(self):
        self.assertEqual(moeda(Decimal("-1234.50")), "R$ -1.234,50")
        self.assertEqual(moeda(Decimal("0")), "R$ 0,00")

    def test_csv(self):
        with tempfile.TemporaryDirectory() as pasta:
            destino = Path(pasta) / "movimentacoes.csv"
            exportar_csv(self.extrato, destino)
            conteudo = destino.read_text(encoding="utf-8-sig")
            self.assertEqual(len(conteudo.splitlines()), 16)
            self.assertIn("01/10/2026;4500,00;RECEBIMENTO", conteudo)

    def test_extrato_inexistente_retorna_erro(self):
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "nao_existe.ofx"
            self.assertEqual(main(["--arquivo", str(arquivo)]), 1)

    def test_extrato_invalido(self):
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "invalido.ofx"
            arquivo.write_text("Isso não é um extrato.", encoding="utf-8")
            with self.assertRaises(ValueError):
                importar_movimentacoes(arquivo)

    def test_movimentacoes_sem_fitid_repetidas(self):

        texto = '''OFXHEADER:100
DATA:OFXSGML
VERSION:102
<OFX><BANKMSGSRSV1><STMTRS><BANKACCTFROM><BANKID>111
<ACCTID>teste
</BANKACCTFROM><BANKTRANLIST>
<STMTTRN><DTPOSTED>20261001000000
<TRNAMT>-10.00
<MEMO>COMPRA
</STMTTRN>
<STMTTRN><DTPOSTED>20261001000000
<TRNAMT>-10.00
<MEMO>COMPRA
</STMTTRN></BANKTRANLIST></STMTRS></BANKMSGSRSV1></OFX>'''
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "sem_fitid.ofx"
            arquivo.write_text(texto, encoding="utf-8")

            with patch("main.ler_ofx", side_effect=lambda p: _ler_sem_biblioteca(Path(p))):
                movimentos = importar_movimentacoes(arquivo)
            self.assertEqual(len(movimentos), 2)
            self.assertNotEqual(movimentos[0].chave_unica, movimentos[1].chave_unica)

if __name__ == "__main__":
    unittest.main()
