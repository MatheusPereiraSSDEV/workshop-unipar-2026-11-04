# -*- coding: utf-8 -*-
"""
Explorar as camadas com SQL, direto nos arquivos Parquet.

Uso:
    python pipeline/explorar.py                                   -> lista as tabelas disponíveis
    python pipeline/explorar.py "SELECT * FROM bronze_vendas LIMIT 10"
    python pipeline/explorar.py "SELECT canal, COUNT(*) FROM bronze_vendas GROUP BY canal"

Nomes das tabelas: bronze_<tabela>, silver_<tabela> e, na Gold, o próprio nome (fato_vendas, dim_cliente...).
"""
import sys

import pandas as pd

from config import conectar_duckdb

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)

con = conectar_duckdb()
if len(sys.argv) < 2:
    print(con.execute("SELECT table_name AS tabela FROM information_schema.tables ORDER BY 1").df().to_string(index=False))
else:
    print(con.execute(sys.argv[1]).df().to_string(index=False))
