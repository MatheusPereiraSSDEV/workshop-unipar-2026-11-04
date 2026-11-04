# Etapa 8 · Do Gold ao painel no Power BI

## 1. Conectar à camada Gold (Parquet)

O Power BI tem **conector nativo para Parquet**: os tipos de cada coluna (data, número inteiro, decimal, texto) já vêm definidos no arquivo.

1. Abra o **Power BI Desktop**.
2. **Página Inicial → Transformar dados → Gerenciar parâmetros → Novo parâmetro**:
   - Nome: `PastaGold`
   - Tipo: Texto
   - Valor atual: o caminho completo da pasta `dados\gold\` do seu projeto, **terminando com `\`**
     Exemplo: `C:\Users\aluno\Downloads\workshop-etl\dados\gold\`
3. **Nova fonte → Consulta nula** e, na barra de fórmulas, digite:
   ```
   = Parquet.Document(File.Contents(PastaGold & "fato_vendas.parquet"))
   ```
4. Renomeie a consulta para `fato_vendas`.
5. Repita (ou duplique a consulta e troque o nome do arquivo) para: `fato_metas`, `dim_cliente`, `dim_produto`, `dim_canal` e `dim_calendario`.
6. **Fechar e aplicar**.

> Alternativa sem parâmetro: **Obter dados → Parquet** e cole o caminho completo de cada arquivo.
> Com o parâmetro, se a pasta mudar de lugar, você troca o caminho **uma vez só**.

## 2. Relacionamentos (modelo estrela)

Na **Exibição de modelo**, crie as relações. Todas são **um para muitos (1:\*)**, com filtro em **direção única**, da dimensão para a fato:

| Dimensão (lado 1) | Fato (lado \*) |
|---|---|
| `dim_calendario[sk_data]` | `fato_vendas[sk_data]` |
| `dim_cliente[sk_cliente]` | `fato_vendas[sk_cliente]` |
| `dim_produto[sk_produto]` | `fato_vendas[sk_produto]` |
| `dim_canal[sk_canal]` | `fato_vendas[sk_canal]` |
| `dim_calendario[sk_data]` | `fato_metas[sk_data]` |
| `dim_canal[sk_canal]` | `fato_metas[sk_canal]` |

Depois:

- Selecione `dim_calendario` → **Marcar como tabela de datas** → coluna `data`.
- Em **Opções → Carregamento de dados**, desmarque **Data/hora automática**.
- Oculte as colunas `sk_*` das fatos (botão direito → Ocultar na exibição de relatório).
- Em `dim_calendario[mes_nome]`, use **Classificar por coluna → mes**.

## 3. Exercício 10 · Medidas DAX

Crie uma tabela vazia chamada **Medidas** (Página Inicial → Inserir dados → OK). Depois, complete cada medida do arquivo [`medidas.dax`](medidas.dax) e crie no Power BI (Nova medida).

| Medida | O que calcula |
|---|---|
| Faturamento | Soma do valor líquido das vendas |
| Qtd Vendas | Quantidade de linhas da fato de vendas |
| Ticket Médio | Faturamento dividido pela quantidade de vendas |
| Margem | Faturamento menos o custo total |
| Margem % | Margem dividida pelo faturamento |
| Meta | Soma da meta de faturamento |
| % Atingimento | Faturamento dividido pela meta |
| Faturamento Ano Anterior | Faturamento no mesmo período do ano anterior |
| Crescimento % | Variação do faturamento contra o ano anterior |

Dicas:

- Use `DIVIDE ( numerador, denominador )` em vez de `/`: ele não quebra quando o denominador é zero.
- Para o ano anterior, pesquise a função `SAMEPERIODLASTYEAR`. Ela recebe a coluna de data da tabela de calendário.

Formate as medidas de valor como **Moeda (R$)** e as de percentual como **Porcentagem**.

## 4. Painel proposto: "Aurora Eletro · Visão Comercial"

| Área | Visual | Campos |
|---|---|---|
| Topo | 4 cartões (ou um visual **Cartão (novo)** com 4 valores) | Faturamento, Margem %, Ticket Médio, % Atingimento |
| Filtros | Segmentações | `dim_calendario[ano]`, `dim_canal[canal]` |
| Meio, esquerda | Gráfico de linhas e colunas | Eixo: `dim_calendario[ano_mes]`; colunas: Faturamento; linha: Meta |
| Meio, direita | Barras horizontais | `dim_produto[categoria]` × Faturamento |
| Base, esquerda | Matriz | `dim_cliente[cidade]` × Faturamento, Qtd Vendas, Ticket Médio |
| Base, direita | Colunas | `dim_calendario[dia_semana]` × Qtd Vendas |

Dica: dê títulos que **respondem** uma pergunta. Em vez de "Faturamento por categoria", escreva a conclusão que o gráfico mostra.

## 5. Perguntas para responder com o painel

1. Em quais meses a Aurora ficou abaixo da meta? Em qual canal?
2. A Black Friday de 2025 aparece nos dados? Quanto representou em relação à média mensal?
3. Qual categoria tem o maior faturamento e qual tem a melhor margem? São a mesma?
4. Fim de semana vende mais que dia útil?
5. Quanto do faturamento está em clientes "não identificados"? Por que isso importa?
