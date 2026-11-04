# -*- coding: utf-8 -*-
"""Orquestrador: executa o pipeline completo, na ordem, e para no primeiro erro."""
import runpy
import sys
import time
from pathlib import Path

ETAPAS = ["01_extract_bronze.py", "02_transform_silver.py", "03_modelagem_gold.py", "04_qualidade.py"]
PASTA = Path(__file__).resolve().parent
sys.path.insert(0, str(PASTA))

inicio = time.time()
for etapa in ETAPAS:
    try:
        runpy.run_path(str(PASTA / etapa), run_name="__main__")
    except SystemExit as e:
        if e.code:
            print(f"\nPipeline interrompido em {etapa}: testes de qualidade falharam.")
            sys.exit(e.code)
    except Exception as e:
        print(f"\nPipeline interrompido em {etapa}: {type(e).__name__}: {e}")
        print("Dica: procure os trechos ____ ainda não preenchidos nesse arquivo.")
        sys.exit(1)
print(f"\nPipeline concluído em {time.time() - inicio:.1f} s")
