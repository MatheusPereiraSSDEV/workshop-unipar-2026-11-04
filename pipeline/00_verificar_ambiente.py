# -*- coding: utf-8 -*-
"""ETAPA 3 - Preparação do ambiente: confere Python, bibliotecas e arquivos de origem."""
import importlib
import platform

from config import ORIGEM, titulo

titulo("Verificação do ambiente")
ok = True

versao = tuple(int(x) for x in platform.python_version().split(".")[:2])
print(f"Python ............ {platform.python_version()}  {'OK' if versao >= (3, 9) else 'ATUALIZE PARA 3.9+'}")
ok &= versao >= (3, 9)

for lib, uso in (("pandas", "tratamento"), ("pyarrow", "leitura e gravação Parquet"),
                 ("openpyxl", "leitura de Excel"), ("duckdb", "SQL sobre Parquet")):
    try:
        mod = importlib.import_module(lib)
        print(f"{lib:<18}{mod.__version__:<10} OK  ({uso})")
    except ImportError:
        print(f"{lib:<18}NÃO ENCONTRADO -> rode: pip install -r requirements.txt")
        ok = False

for arq in ("vendas.csv", "clientes.xlsx", "produtos.csv", "metas.xlsx"):
    existe = (ORIGEM / arq).exists()
    print(f"{arq:<18}{'encontrado' if existe else 'FALTANDO em dados/origem'}")
    ok &= existe

print("\nTudo pronto para começar!" if ok else "\nCorrija os itens acima antes de seguir.")
