-- =====================================================================
-- ETAPA 6 - MODELAGEM (camada Gold) - SQL com DuckDB
-- Modelo dimensional (estrela): fatos no centro, dimensões ao redor.
-- O Python cria views que leem os arquivos da Silver:
--   silver_vendas, silver_clientes, silver_produtos, silver_metas
-- Ao final, cada tabela abaixo é gravada em dados/gold/<tabela>.parquet
-- =====================================================================

-- ---------------------------------------------------------------------
-- dim_cliente: chave substituta (sk) + membro "não identificado" (sk = 0)
-- ---------------------------------------------------------------------
CREATE OR REPLACE TABLE dim_cliente AS
SELECT 0 AS sk_cliente, 'N/I' AS id_cliente, 'Cliente não identificado' AS nome,
       'Não informada' AS cidade, 'N/I' AS uf, 'Não informado' AS segmento,
       CAST(NULL AS DATE) AS data_cadastro
UNION ALL
SELECT ROW_NUMBER() OVER (ORDER BY id_cliente) AS sk_cliente,
       id_cliente, nome, cidade, uf, segmento,
       CAST(data_cadastro AS DATE)
FROM silver_clientes;

-- ---------------------------------------------------------------------
-- dim_produto
-- ---------------------------------------------------------------------
-- EXERCÍCIO 7: carregue a dim_produto a partir de silver_produtos (mesmo padrão da dim_cliente)
CREATE OR REPLACE TABLE dim_produto AS
SELECT 0 AS sk_produto, 'N/I' AS id_produto, 'Produto não identificado' AS descricao,
       'Não informada' AS categoria, CAST(NULL AS DOUBLE) AS preco_venda,
       CAST(NULL AS DOUBLE) AS preco_custo, 'N' AS ativo
UNION ALL
SELECT ROW_NUMBER() OVER (ORDER BY id_produto),
       id_produto, descricao, categoria, preco_venda, preco_custo, ativo
FROM silver_produtos;

-- ---------------------------------------------------------------------
-- dim_canal
-- ---------------------------------------------------------------------
CREATE OR REPLACE TABLE dim_canal AS
SELECT ROW_NUMBER() OVER (ORDER BY canal) AS sk_canal, canal
FROM (SELECT canal FROM silver_vendas WHERE canal IS NOT NULL
      UNION
      SELECT canal FROM silver_metas WHERE canal IS NOT NULL);

-- ---------------------------------------------------------------------
-- dim_calendario: uma linha por dia, do 1º dia do primeiro ano ao último dia do último ano
-- ---------------------------------------------------------------------
CREATE OR REPLACE TABLE dim_calendario AS
WITH dias AS (
    SELECT CAST(UNNEST(generate_series(
               date_trunc('year', MIN(data_venda)),
               date_trunc('year', MAX(data_venda)) + INTERVAL 1 YEAR - INTERVAL 1 DAY,
               INTERVAL 1 DAY)) AS DATE) AS data
    FROM silver_vendas
)
SELECT
    CAST(strftime(data, '%Y%m%d') AS INTEGER) AS sk_data,
    data,
    year(data)                                AS ano,
    month(data)                               AS mes,
    ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'][month(data)] AS mes_nome,
    strftime(data, '%Y-%m')                   AS ano_mes,
    'T' || quarter(data)                      AS trimestre,
    dayofweek(data)                           AS dia_semana_num,
    ['dom', 'seg', 'ter', 'qua', 'qui', 'sex', 'sáb'][dayofweek(data) + 1] AS dia_semana,
    CASE WHEN dayofweek(data) IN (0, 6) THEN 'Fim de semana' ELSE 'Dia útil' END AS tipo_dia
FROM dias
ORDER BY data;

-- ---------------------------------------------------------------------
-- fato_vendas: grão = uma linha por venda concluída
-- ---------------------------------------------------------------------
-- EXERCÍCIO 8: complete os JOINs para trocar os códigos de negócio pelas chaves substitutas.
--   Vendas sem cliente/produto correspondente devem apontar para o membro 0 (COALESCE).
CREATE OR REPLACE TABLE fato_vendas AS
SELECT
    v.id_venda,
    CAST(strftime(v.data_venda, '%Y%m%d') AS INTEGER) AS sk_data,
    COALESCE(c.sk_cliente, 0)                         AS sk_cliente,
    COALESCE(p.sk_produto, 0)                         AS sk_produto,
    COALESCE(k.sk_canal, 0)                           AS sk_canal,
    v.quantidade,
    v.valor_unitario,
    v.valor_bruto,
    v.valor_desconto,
    v.valor_liquido,
    ROUND(v.quantidade * p.preco_custo, 2)            AS custo_total
FROM silver_vendas v
LEFT JOIN dim_cliente c ON c.id_cliente = v.id_cliente
LEFT JOIN dim_produto p ON p.id_produto = v.id_produto
LEFT JOIN dim_canal   k ON k.canal = v.canal
WHERE v.status = 'Concluída'
ORDER BY v.id_venda;

-- ---------------------------------------------------------------------
-- fato_metas: grão = mês x canal
-- ---------------------------------------------------------------------
CREATE OR REPLACE TABLE fato_metas AS
SELECT
    CAST(strftime(m.data_mes, '%Y%m%d') AS INTEGER) AS sk_data,
    k.sk_canal,
    m.meta_faturamento
FROM silver_metas m
JOIN dim_canal k ON k.canal = m.canal;
