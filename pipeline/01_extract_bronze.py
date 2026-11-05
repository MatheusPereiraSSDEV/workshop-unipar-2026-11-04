# -*- coding: utf-8 -*-
"""
ETAPA 4 - EXTRACT (camada Bronze)

Regra de ouro da Bronze: o dado entra EXATAMENTE como veio da fonte.
Nada de corrigir, converter ou filtrar aqui. Só acrescentamos colunas de controle
para saber de onde o dado veio e quando foi carregado.

Saída: um arquivo Parquet por fonte, em dados/bronze/
"""
from datetime import datetime

import pandas as pd

from config import ORIGEM, arquivo, gravar, titulo

# Cada fonte tem o seu jeito: separador, codificação, formato de arquivo...
FONTES = [
    # tabela      arquivo                       opções de leitura
    ("vendas",   ORIGEM / "vendas.csv",   {"sep": ",", "encoding": "utf-8"}),      # exportação do ERP
    ("clientes", ORIGEM / "clientes.xlsx", {}),                                    # planilha do CRM
    ("produtos", ORIGEM / "produtos.csv", {"sep": ";", "encoding": "latin-1"}),    # sistema antigo
    ("metas",    ORIGEM / "metas.xlsx",    {}),                                    # planejamento comercial
]


def ler_fonte(caminho, opcoes):
    """Lê CSV ou Excel trazendo TODAS as colunas como texto (dtype=str)."""
    if caminho.suffix == ".xlsx":
        return pd.read_excel(caminho, dtype=str)
    return pd.read_csv(caminho, dtype=str, **opcoes)


def main():
    titulo("EXTRACT -> Bronze (Parquet)")
    carga = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for tabela, caminho, opcoes in FONTES:
        df = ler_fonte(caminho, opcoes)

        # EXERCÍCIO 1: adicione as colunas de controle
        #   _origem      -> nome do arquivo de origem (ex.: vendas.csv)
        #   _data_carga  -> data e hora desta carga (variável carga)
        df["_origem"] = caminho.name
        df["_data_carga"] = carga

        gravar(df, "bronze", tabela)
        print(f"  {tabela:<10} {len(df):>6} linhas  {caminho.name:<14} -> {arquivo('bronze', tabela).name}")
    print(f"\nArquivos gerados em: {arquivo('bronze', 'x').parent}")


if __name__ == "__main__":
    main()
