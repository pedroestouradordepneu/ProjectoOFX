# ProjetoOFX

**Pedro Henrique Breda Domingues — RA 25000578**

Desenvolvi uma aplicação em Python para ler arquivos OFX, exibir movimentações e calcular entradas, saídas e saldo. Também implementei relatórios e importação para PostgreSQL com prevenção de duplicatas.

## Execução

Instalo as dependências e executo:

```bash
pip install -r requirements.txt
python main.py
```

Para exportar os relatórios, uso:

```bash
python main.py --salvar resultado_extrato.txt --csv movimentacoes.csv
```

Para importar no PostgreSQL, configuro meu `.env` a partir do `.env.example` e executo:

```bash
python main.py --postgres
```

Confiro os registros no DBeaver com `consultas_dbeaver.sql`.

## Testes

Executo:

```bash
python -m unittest discover -s tests -v
```

Validei os 11 testes automatizados. Ainda não validei a conexão com PostgreSQL real.
