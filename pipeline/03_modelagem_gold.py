# -*- coding: utf-8 -*-
"""
ETAPA 6 - MODELAGEM (camada Gold)

Executa o gold.sql no DuckDB, lendo os arquivos Parquet da Silver,
e grava cada tabela do modelo em dados/gold/<tabela>.parquet.
O Power BI lê esses arquivos diretamente (Obter dados -> Parquet).
"""
from pathlib import Path

from config import arquivo, conectar_duckdb, titulo

SQL = Path(__file__).with_name("gold.sql")
TABELAS = ["dim_cliente", "dim_produto", "dim_canal", "dim_calendario", "fato_vendas", "fato_metas"]


def main():
    titulo("MODELAGEM -> Gold (SQL com DuckDB)")
    con = conectar_duckdb(["silver"])            # views silver_* sobre os arquivos Parquet
    con.execute(SQL.read_text(encoding="utf-8"))
    for t in TABELAS:
        destino = arquivo("gold", t)
        con.execute(f"COPY {t} TO '{destino.as_posix()}' (FORMAT PARQUET)")
        n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t:<16} {n:>6} linhas  -> {destino.name}")
    con.close()
    print(f"\nArquivos gerados em: {arquivo('gold', 'x').parent}")


if __name__ == "__main__":
    main()
