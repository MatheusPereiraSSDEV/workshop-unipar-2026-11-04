"""Caminhos e utilitários compartilhados por todas as etapas do pipeline."""
import sys
from pathlib import Path

import pandas as pd


try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

RAIZ = Path(__file__).resolve().parents[1]
DADOS = RAIZ / "dados"
ORIGEM = DADOS / "origem"
CAMADAS = {c: DADOS / c for c in ("bronze", "silver", "gold")}

for pasta in CAMADAS.values():
    pasta.mkdir(parents=True, exist_ok=True)


def arquivo(camada, tabela):
    """Caminho do arquivo Parquet de uma tabela. Ex.: dados/silver/vendas.parquet"""
    return CAMADAS[camada] / f"{tabela}.parquet"


def gravar(df, camada, tabela):
    """Grava a tabela em Parquet: colunar, comprimido e com os tipos de cada coluna."""
    df.to_parquet(arquivo(camada, tabela), index=False)


def ler(camada, tabela):
    return pd.read_parquet(arquivo(camada, tabela))


def conectar_duckdb(camadas=("bronze", "silver", "gold")):
    """
    Abre o DuckDB em memória e cria uma view para cada arquivo Parquet:
    bronze_vendas, silver_clientes, fato_vendas, dim_produto...
    Assim dá para consultar os arquivos com SQL, como se fossem tabelas.
    """
    import duckdb
    con = duckdb.connect()
    for camada in camadas:
        for arq in sorted(CAMADAS[camada].glob("*.parquet")):
            nome = arq.stem if camada == "gold" else f"{camada}_{arq.stem}"
            con.execute(f"CREATE OR REPLACE VIEW {nome} AS SELECT * FROM read_parquet('{arq.as_posix()}')")
    return con


def titulo(texto):
    print("\n" + "=" * 70 + f"\n{texto}\n" + "=" * 70)
