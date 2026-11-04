# Do dado bruto ao dashboard: ETL na prática

**Workshop acadêmico · UNIPAR · Softwaresul**
Python, Parquet e Power BI

Neste projeto você vai construir um pipeline ETL completo para a **Aurora Eletro**, uma rede de lojas de eletrônicos **fictícia** do Paraná. Os dados chegam de quatro fontes diferentes, cheios de problemas, e saem organizados em camadas Bronze, Silver e Gold, gravadas em **arquivos Parquet**, até virarem um painel no Power BI.

> Todos os dados deste pacote são fictícios. Nenhum dado real de clientes ou empresas é usado.

---

## 1. O que você precisa

| Ferramenta | Para quê | Como instalar |
|---|---|---|
| Python 3.9 ou superior | Extração, tratamento e orquestração | [python.org/downloads](https://www.python.org/downloads/). No Windows, marque **Add python.exe to PATH**. Não precisa ser administrador. |
| pandas, pyarrow, openpyxl, duckdb | Tratar dados, gravar Parquet, ler Excel e rodar SQL sobre os arquivos | `pip install -r requirements.txt` |
| Power BI Desktop | Modelo e painel | Microsoft Store ou [powerbi.microsoft.com](https://powerbi.microsoft.com/desktop). Somente Windows. |
| Editor de código (opcional) | Editar os scripts | VS Code, PyCharm ou o próprio IDLE do Python |

Quem usa macOS ou Linux faz todo o pipeline normalmente e acompanha a parte de Power BI em dupla com um colega que usa Windows.

### Por que Parquet?

| | CSV | Parquet |
|---|---|---|
| Formato | Texto, linha a linha | Binário, **colunar** e comprimido |
| Tipos | Tudo é texto; cada programa interpreta do seu jeito | Cada coluna guarda o seu tipo: data, número, texto |
| Tamanho | `vendas.csv`: cerca de 400 KB | `vendas.parquet`: cerca de 90 KB |
| Power BI | Precisa acertar separador, codificação e vírgula decimal | Conector nativo: lê direto, com os tipos certos |
| No mercado | Troca de arquivos entre sistemas | Base de Data Lakes e Lakehouses (Delta Lake, Microsoft Fabric) |

E o SQL? O **DuckDB** executa SQL direto sobre os arquivos Parquet, sem servidor de banco. É o que usamos para montar a camada Gold.

## 2. Estrutura do projeto

```
workshop-etl/
├── dados/
│   ├── origem/        <- arquivos recebidos das "fontes" (não altere)
│   ├── bronze/        <- *.parquet: cópia fiel das fontes
│   ├── silver/        <- *.parquet: dados tratados
│   └── gold/          <- *.parquet: modelo dimensional, lido pelo Power BI
├── pipeline/          <- VOCÊ TRABALHA AQUI (scripts com exercícios)
├── powerbi/           <- guia do painel e medidas DAX para completar
├── CASOS_DE_USO.md    <- outros cenários e desafios extras
└── requirements.txt
```

As fontes de dados:

| Arquivo | Simula | Detalhe técnico |
|---|---|---|
| `vendas.csv` | Exportação do ERP | Separador `,`, UTF-8 |
| `clientes.xlsx` | Planilha do CRM | Excel |
| `produtos.csv` | Sistema legado | Separador `;`, codificação **latin-1** |
| `metas.xlsx` | Planejamento comercial | Meta mensal por canal |

## 3. Passo a passo

Abra um terminal **na pasta do projeto** e execute cada etapa com `python pipeline/<arquivo>.py`.
No Windows, se `python` não funcionar, use `py`.

Os exercícios são trechos marcados com `____` para você completar. O comentário logo acima de cada trecho explica o que fazer.

### Etapa 3 · Preparar o ambiente

```bash
pip install -r requirements.txt
python pipeline/00_verificar_ambiente.py
```

Tudo precisa aparecer como OK antes de seguir.

### Etapa 4 · Extract → Bronze (`01_extract_bronze.py`)

Lê as quatro fontes **como texto** e grava um arquivo Parquet por fonte em `dados/bronze/`, sem alterar nada.

- **Exercício 1:** crie as colunas de controle `_origem` e `_data_carga`.

> Por que tudo como texto? Na Bronze não interpretamos nada. Se o pandas "adivinhar" um tipo, ele pode perder informação, como o zero à esquerda de um código ou uma data em outro formato.

Para olhar os dados com SQL, a qualquer momento:

```bash
python pipeline/explorar.py "SELECT * FROM bronze_vendas LIMIT 10"
python pipeline/explorar.py "SELECT canal, COUNT(*) AS n FROM bronze_vendas GROUP BY canal"
```

### Etapa 5 · Transform → Silver (`02_transform_silver.py`)

| Exercício | Problema real nos dados |
|---|---|
| 2 | Datas em dois formatos (`2025-03-15` e `15/03/2025`) e datas impossíveis (`2025-02-30`) |
| 3 | Números no padrão brasileiro (`1.299,90`) misturados com o americano (`1299.90`) |
| 4 | Linhas repetidas na exportação |
| 5 | Canal de venda escrito de vários jeitos diferentes |
| 6 | Valor da venda não vem calculado: bruto, desconto e líquido |

Registros que não podem ser corrigidos **não são apagados**: vão para `vendas_rejeitadas`, com o motivo. Em projetos reais, essa "quarentena" é revisada pelo time de negócio.

### Etapa 6 · Modelagem → Gold (`03_modelagem_gold.py` + `gold.sql`)

O modelo dimensional é criado **em SQL, com DuckDB**, lendo os Parquet da Silver:

- `dim_cliente`, `dim_produto`, `dim_canal` com **chave substituta** (`sk_`) e um membro `0 = não identificado`
- `dim_calendario`, um dia por linha
- `fato_vendas` (uma linha por venda concluída) e `fato_metas` (mês × canal)

- **Exercício 7:** carregar a `dim_produto`.
- **Exercício 8:** completar os `LEFT JOIN` da fato com as dimensões.

Cada tabela é gravada em `dados/gold/<tabela>.parquet`.

### Etapa 7 · Qualidade (`04_qualidade.py`)

Testes de contagem, chaves únicas, integridade referencial e faixas de valores. Se algo falhar, o script termina com erro.

- **Exercício 9:** escrever o teste de integridade entre `fato_vendas` e `dim_produto`.

### Rodar tudo de uma vez

```bash
python pipeline/run_pipeline.py
```

### Etapa 8 · Power BI

Siga o arquivo [`powerbi/GUIA_POWERBI.md`](powerbi/GUIA_POWERBI.md). O **exercício 10** é completar as medidas DAX.

### Etapa 9 · Antes x depois

```bash
python pipeline/05_antes_depois.py
```

Compara o mesmo indicador calculado direto do arquivo bruto e a partir da camada Gold.

## 4. Problemas comuns

| Sintoma | Causa provável | Solução |
|---|---|---|
| `'python' não é reconhecido` | Python fora do PATH | Use `py` ou reinstale marcando *Add to PATH* |
| `NameError: name '____' is not defined` | Exercício ainda não preenchido | Procure os `____` no arquivo indicado |
| `Parser Error` ou `syntax error at or near "____"` | Exercício de SQL não preenchido | Complete os `____` do `gold.sql` |
| `ImportError: Unable to find a usable engine` | pyarrow não instalado | `pip install -r requirements.txt` |
| `UnicodeDecodeError` ao ler produtos | Codificação errada | O arquivo é `latin-1`, não UTF-8 |
| `FileNotFoundError` em `dados/...parquet` | Etapa anterior não foi executada | Rode as etapas na ordem |
| Travou e a turma já seguiu | Acontece | Peça ao instrutor o arquivo da etapa e continue |

## 5. Para continuar estudando

Veja [`CASOS_DE_USO.md`](CASOS_DE_USO.md): outros cenários reais e desafios para evoluir este pipeline.
