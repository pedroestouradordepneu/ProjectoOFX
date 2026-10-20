# ProjetoOFX — Leitura de Extratos Bancários com Python

Aplicação desenvolvida para a atividade **Leitura de Arquivos OFX com Python**. O programa interpreta movimentações financeiras de um arquivo `.ofx`, apresenta data, valor e descrição, conta as transações, calcula os totais e permite exportá-las para CSV e importar para PostgreSQL **sem repetir lançamentos já inseridos**.

## Funcionalidades

- Leitura de OFX bancário utilizando a biblioteca **ofxparse**; há um leitor básico de reserva para execução didática quando a biblioteca não está instalada.
- Exibição da data, valor e descrição de cada movimentação.
- Contagem de movimentações, soma das entradas, saídas (valores negativos) e saldo líquido do **período**.
- Formatação dos valores em reais (`R$ 1.234,56`).
- Exportação opcional para **TXT** e **CSV**.
- Importação opcional para **PostgreSQL** com `psycopg2`, transação SQL e prevenção de duplicatas com identificador único (`FITID`/SHA-256).
- Testes automatizados com a biblioteca padrão `unittest`.

## Estrutura do projeto

```text
ProjetoOFX/
├── main.py                      # Entrada principal, relatório e exportação
├── leitor_ofx.py                # Leitura OFX com ofxparse
├── banco.py                     # Inserção no PostgreSQL
├── extrato.ofx                  # Exemplo fornecido, conta anonimizada
├── schema.sql                   # Estrutura da tabela e restrição UNIQUE
├── consultas_dbeaver.sql       # Consultas para conferir os registros
├── movimentacoes.csv           # Exemplo de CSV gerado
├── resultado_extrato.txt        # Exemplo do relatório gerado
├── requirements.txt            # Bibliotecas externas
├── .env.example                 # Configuração de conexão, sem credenciais
├── .gitignore                   # Exclui senhas, venv e caches
├── executar_windows.bat        # Atalho para execução no Windows
├── evidencias/
│   └── testes_automaticos.txt  # Registro de testes executados
└── tests/
    └── test_projeto.py         # Testes unitários
```

## Requisitos

- Python **3.10 ou superior** instalado.
- VS Code ou qualquer terminal.
- Opcional para o desafio extra: PostgreSQL e DBeaver.

## 1. Como executar no Windows

Abra a pasta `ProjetoOFX` no VS Code e execute no terminal:

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
py main.py
```

> Caso o PowerShell bloqueie a ativação, não é necessário ativar o ambiente virtual: execute `venv\Scripts\python.exe -m pip install -r requirements.txt` e depois `venv\Scripts\python.exe main.py`.
>
> Você também pode dar dois cliques em `executar_windows.bat`; ele chama o Python disponível e mantém a janela aberta.

Se você preferir o terminal CMD, a ativação é `venv\Scripts\activate.bat`. O comando `python main.py` também funciona se o Python estiver no PATH.

## 2. Resultado do arquivo fornecido

O arquivo de exemplo contém 15 movimentações realizadas em outubro de 2026. Para visualizar os lançamentos completos, abra `resultado_extrato.txt` ou execute `py main.py`.

| Indicador | Valor |
| --- | ---: |
| Movimentações | **15** |
| Entradas | **R$ 17.900,00** |
| Saídas | **R$ -6.059,70** |
| Saldo das movimentações | **R$ 11.840,30** |

O saldo calculado é a **variação líquida no período**, não necessariamente o saldo disponível na conta bancária.

Para gerar novamente os arquivos de relatório:

```powershell
py main.py --salvar resultado_extrato.txt --csv movimentacoes.csv
```

Para utilizar outro OFX:

```powershell
py main.py --arquivo caminho\para\outro_extrato.ofx
```

## 3. Desafio extra — PostgreSQL e DBeaver

1. Crie um banco chamado `projeto_ofx` no PostgreSQL. No DBeaver, conecte-se ao PostgreSQL e execute:

   ```sql
   CREATE DATABASE projeto_ofx;
   ```

   > Rode esse comando conectado ao banco padrão `postgres` e depois abra uma conexão ou editor SQL apontando para `projeto_ofx`.
2. Copie `.env.example` para `.env` e troque `PGPASSWORD` pela **sua senha local**. Se for um PostgreSQL remoto, ajuste `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER` e `PGSSLMODE` conforme seu provedor.
3. Instale as dependências e execute:

   ```powershell
   py -m pip install -r requirements.txt
   py main.py --postgres
   ```

4. O programa criará (se necessário) a tabela `movimentacoes` usando `schema.sql`, gravará os lançamentos e informará quantos são novos e quantos já existiam.
5. No **DBeaver**, abra o arquivo `consultas_dbeaver.sql` e execute cada consulta para verificar os 15 registros, os totais e as duplicatas.
6. Rode `py main.py --postgres` **uma segunda vez**: com os mesmos dados, o resultado esperado é `0` inseridos e `15` duplicados ignorados.

A estrutura pedida pelo professor foi mantida (`id`, `data_movimentacao`, `valor`, `descricao`) e acrescentou-se `chave_unica VARCHAR(64)` com restrição **UNIQUE** para cumprir o desafio bônus. As consultas SQL ficam no arquivo `consultas_dbeaver.sql`.

### Validação de duplicatas

Quando há `FITID` (identificador original de transação do OFX), ele é combinado com a identidade da conta e convertido em uma chave SHA-256. Se não houver `FITID`, usa-se um identificador derivado de data, valor, descrição e posição entre ocorrências iguais dentro do arquivo. Esse caso de fallback evita duplicar **o mesmo arquivo**, mas não garante identificação perfeita entre arquivos com extratos sobrepostos quando faltam IDs bancários.

## 4. Executar os testes

```powershell
py -m unittest discover -s tests -v
```

Os testes cobrem: quantidade, totais, datas e valores, chaves de duplicação, importação repetida por meio de **banco simulado**, relatórios, moeda, CSV e arquivos inválidos. Veja `evidencias/testes_automaticos.txt`.

**Limite da validação:** os testes unitários foram executados; a conexão a um PostgreSQL real e a conferência com DBeaver exigem um servidor e credenciais locais que não estão incluídos no projeto. Não foram apresentados prints de conexão real nem dados inventados.

## 5. Enviar ao GitHub com seus próprios commits

O ZIP já inclui uma pasta `.git` com um histórico de commits e nome de autor **Pedro Henrique Breda Domingues**. Para publicar:

1. Extraia a pasta `ProjetoOFX` (inclusive a pasta oculta `.git`).
2. Abra o **GitHub Desktop** → **File** → **Add Local Repository** e escolha `ProjetoOFX`.
3. Antes de publicar, configure o **e-mail de autor da sua conta GitHub**. A autoria pelo nome já existe, mas a associação dos commits ao seu perfil depende desse e-mail.
4. Use **Publish repository** e copie o link público gerado como entrega da atividade.

Se você quiser corrigir o e-mail de **todos os commits antes do primeiro envio**, rode o terminal Git na pasta (substitua pelo seu e-mail confirmado nas configurações do GitHub):

```bash
git config user.name "Pedro Henrique Breda Domingues"
git config user.email "SEU_EMAIL_CONFIRMADO_NO_GITHUB"
git rebase --root --exec "git commit --amend --no-edit --reset-author"
```

> Altere o e-mail **antes** de publicar. Reescrever um histórico que já está publicado precisa de cuidado. E-mails de exemplo não garantem associação ao perfil.

## Conceito de ETL demonstrado

- **Extração:** ler o arquivo OFX.
- **Transformação:** normalizar datas, valores em `Decimal`, descrição e identificação única.
- **Carga:** exibir/exportar os resultados e gravar no PostgreSQL (opcional).

## Privacidade

Para viabilizar a entrega em um GitHub público, os identificadores de **banco, agência e conta** do arquivo de exemplo foram anonimizados. Os 15 lançamentos, suas descrições, datas e valores foram mantidos para reproduzir a atividade. Nunca publique extratos reais, senhas de banco ou seu arquivo `.env` em repositórios públicos.

**Autor:** Pedro Henrique Breda Domingues.
