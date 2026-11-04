# Casos de uso: ETL fora da sala de aula

O pipeline da Aurora Eletro segue o mesmo desenho usado em projetos corporativos. Abaixo, outros cenários comuns no Paraná e no mercado de dados, organizados do mesmo jeito: **fontes → problemas típicos → camadas → indicadores**.

---

## Caso 0 · Varejo: Aurora Eletro (o caso da aula)

**Pergunta de negócio:** estamos batendo a meta? Em qual canal, categoria e cidade?

| Camada | O que acontece |
|---|---|
| Fontes | ERP (vendas), CRM (clientes), sistema legado (produtos), planilha de metas |
| Bronze | Cópia fiel das quatro fontes, com `_origem` e `_data_carga` |
| Silver | Datas em dois formatos, número brasileiro, canal escrito de 11 jeitos, cidade sem acento, cliente duplicado, quarentena |
| Gold | `fato_vendas`, `fato_metas`, `dim_cliente`, `dim_produto`, `dim_canal`, `dim_calendario` |
| Indicadores | Faturamento, margem, ticket médio, % de atingimento da meta, crescimento ano contra ano |

---

## Caso 1 · Agronegócio: recebimento de grãos em uma cooperativa

**Contexto:** a cooperativa recebe soja e milho em várias unidades. Cada caminhão passa pela balança e pelo laboratório de classificação.

| Etapa | Detalhes |
|---|---|
| Fontes | Balança (CSV por unidade), laboratório (umidade e impureza, Excel), cadastro de cooperados (sistema), cotação diária (API) |
| Problemas típicos | Peso em kg numa unidade e em sacas noutra; placa digitada de formas diferentes; umidade com vírgula e ponto; pesagem duplicada quando o caminhão passa duas vezes; cooperado sem cadastro |
| Silver | Converter tudo para kg; calcular desconto de umidade e impureza; padronizar placa; quarentena para pesagens sem laudo |
| Gold | `fato_recebimento` (por carga), `dim_cooperado`, `dim_unidade`, `dim_produto`, `dim_calendario`, `fato_cotacao` |
| Indicadores | Toneladas recebidas por safra, umidade média por região, valor estimado do estoque, ranking de cooperados |

---

## Caso 2 · Saúde: faltas em consultas de uma rede de clínicas

**Contexto:** horários vagos por falta de paciente geram custo e aumentam a fila.

| Etapa | Detalhes |
|---|---|
| Fontes | Agenda (sistema da clínica), cadastro de pacientes, confirmações por WhatsApp (exportação), convênios |
| Problemas típicos | Mesmo paciente com dois cadastros (CPF com e sem pontuação); horário com fuso diferente; status escrito de formas distintas |
| Silver | Unificar pacientes por CPF; **anonimizar** nome e CPF (LGPD) antes da Gold; padronizar status |
| Gold | `fato_agendamento`, `dim_paciente` (faixa etária, bairro, sem dados pessoais), `dim_especialidade`, `dim_profissional`, `dim_calendario` |
| Indicadores | Taxa de faltas por especialidade, dia da semana e antecedência do agendamento; efeito da confirmação por mensagem |

> Ponto de discussão: quais colunas podem chegar ao painel e quais devem ficar só na Silver?

---

## Caso 3 · Educação: risco de evasão na graduação

**Contexto:** a coordenação quer agir antes que o aluno abandone o curso.

| Etapa | Detalhes |
|---|---|
| Fontes | Matrículas, frequência por aula, notas, acessos ao ambiente virtual, financeiro |
| Problemas típicos | Turmas com código diferente entre sistemas; frequência lançada em atraso; notas em escalas diferentes (0 a 10 e 0 a 100) |
| Silver | Uniformizar escala de notas; consolidar frequência por semana; criar a regra de "aluno ativo" |
| Gold | `fato_frequencia_semanal`, `fato_nota`, `dim_aluno` (sem dados sensíveis), `dim_disciplina`, `dim_turma`, `dim_calendario` |
| Indicadores | Frequência média por turma, alunos com 3 faltas seguidas, alunos sem acesso ao ambiente há 15 dias, evolução por período |

---

## Caso 4 · Indústria: eficiência de linha de produção (OEE)

**Contexto:** uma indústria de alimentos quer saber por que a linha produz menos do que a capacidade.

| Etapa | Detalhes |
|---|---|
| Fontes | Apontamentos de produção (MES), paradas registradas pelos operadores, controle de qualidade, turnos |
| Problemas típicos | Parada sem motivo informado; horário de fim antes do início; motivos escritos livremente |
| Silver | Corrigir intervalos inválidos; classificar paradas por motivo padrão; calcular minutos disponíveis por turno |
| Gold | `fato_producao`, `fato_parada`, `dim_linha`, `dim_produto`, `dim_turno`, `dim_motivo_parada`, `dim_calendario` |
| Indicadores | OEE = disponibilidade × performance × qualidade; top 5 motivos de parada; perdas por turno |

---

## Desafios para evoluir o pipeline da Aurora

Do mais simples ao mais avançado:

1. **Nova regra de qualidade:** adicione em `04_qualidade.py` um teste que falhe se alguma venda tiver data no futuro.
2. **Nova coluna na dimensão:** crie `faixa_preco` na `dim_produto` (até R$ 500, até R$ 2.000, acima disso) usando `CASE WHEN` no SQL.
3. **Relatório de quarentena:** exporte `vendas_rejeitadas` para Excel e crie uma página no Power BI para o time de negócio revisar.
4. **Margem por canal:** a meta é de faturamento. Proponha e implemente uma meta de margem.
5. **Carga incremental:** hoje a Bronze é recriada a cada execução. Altere para gravar só as vendas com `id_venda` que ainda não existem.
6. **Nova fonte:** simule um arquivo `devolucoes.csv` (id_venda, data, motivo) e leve as devoluções até a Gold, descontando do faturamento.
7. **Orquestração:** agende o `run_pipeline.py` no Agendador de Tarefas do Windows (ou `cron`) e registre um log de cada execução.

---

## Do workshop para o mercado

| No workshop | Em uma empresa |
|---|---|
| Arquivos CSV e Excel na pasta | APIs, bancos transacionais, eventos em tempo real |
| pandas | pandas, PySpark, Dataflows, SQL em escala |
| Pastas bronze, silver e gold com arquivos Parquet | Data Lake ou Lakehouse (OneLake, S3, ADLS) com tabelas Delta, que também são Parquet por baixo |
| DuckDB rodando SQL sobre os arquivos | SQL em Warehouse ou endpoint SQL do Lakehouse, Spark SQL |
| `run_pipeline.py` | Orquestradores: Data Factory, Airflow, Fabric Pipelines |
| `04_qualidade.py` | Testes automatizados (dbt tests, Great Expectations) e alertas |
| Power BI Desktop | Power BI Service ou Microsoft Fabric, com atualização agendada, segurança e governança |
