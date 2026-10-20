

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import Movimentacao

PASTA = Path(__file__).resolve().parent
INSERT_SQL = """
INSERT INTO movimentacoes (data_movimentacao, valor, descricao, chave_unica)
VALUES (%s, %s, %s, %s)
ON CONFLICT (chave_unica) DO NOTHING
RETURNING id;
"""

def gravar_movimentacoes(
    movimentacoes: list[Movimentacao], conexao=None
) -> tuple[int, int]:

    propria_conexao = conexao is None
    if propria_conexao:
        try:
            from dotenv import load_dotenv
            import psycopg2
        except ImportError as erro:
            raise ImportError(
                "Instale as dependências: pip install -r requirements.txt"
            ) from erro
        load_dotenv(PASTA / ".env")
        configuracao = {
            "host": os.getenv("PGHOST", "localhost"),
            "port": int(os.getenv("PGPORT", "5432")),
            "dbname": os.getenv("PGDATABASE", "projeto_ofx"),
            "user": os.getenv("PGUSER", "postgres"),
            "password": os.getenv("PGPASSWORD", ""),
            "connect_timeout": 10,
        }
        sslmode = os.getenv("PGSSLMODE", "")
        if sslmode:
            configuracao["sslmode"] = sslmode
        conexao = psycopg2.connect(**configuracao)

    inseridas = 0
    ignoradas = 0
    try:
        with conexao:
            with conexao.cursor() as cursor:
                cursor.execute((PASTA / "schema.sql").read_text(encoding="utf-8"))
                for mov in movimentacoes:
                    cursor.execute(
                        INSERT_SQL,
                        (mov.data, mov.valor, mov.descricao[:255], mov.chave_unica),
                    )
                    if cursor.fetchone() is None:
                        ignoradas += 1
                    else:
                        inseridas += 1
        return inseridas, ignoradas
    finally:
        if propria_conexao:
            conexao.close()
