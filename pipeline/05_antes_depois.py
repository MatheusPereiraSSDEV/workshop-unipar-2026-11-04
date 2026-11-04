# -*- coding: utf-8 -*-
"""
ETAPA 9 - FECHAMENTO: o mesmo indicador antes e depois do tratamento.

"Antes" = o que alguém calcularia direto do arquivo bruto, sem tratar nada.
"Depois" = o que sai da camada Gold.
"""
import pandas as pd

from config import ler, titulo


def br(v, dec=2):
    """Formata no padrão brasileiro: 1.234.567,89"""
    return f"{v:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def main():
    titulo("ANTES x DEPOIS DO TRATAMENTO")
    bruto, cli_bruto = ler("bronze", "vendas"), ler("bronze", "clientes")
    fato, dim_cli, dim_canal = ler("gold", "fato_vendas"), ler("gold", "dim_cliente"), ler("gold", "dim_canal")
    dim_cli = dim_cli[dim_cli["sk_cliente"] > 0]

    # "Antes": soma ingênua. Valores em formato brasileiro viram vazio, duplicadas e canceladas entram.
    qtd = pd.to_numeric(bruto["quantidade"], errors="coerce")
    preco = pd.to_numeric(bruto["valor_unitario"], errors="coerce")
    fat_bruto = (qtd * preco).sum()
    fat_gold = fato["valor_liquido"].sum()

    linhas = [
        ("Faturamento total", "R$ " + br(fat_bruto), "R$ " + br(fat_gold)),
        ("Quantidade de vendas", br(len(bruto), 0), br(len(fato), 0)),
        ("Canais de venda", f"{bruto['canal'].nunique()}", f"{len(dim_canal)}"),
        ("Cidades de clientes", f"{cli_bruto['cidade'].nunique()}", f"{dim_cli['cidade'].nunique()}"),
        ("Clientes", br(len(cli_bruto), 0), br(len(dim_cli), 0)),
    ]
    print(f"\n  {'Indicador':<24}{'Antes (bruto)':>22}{'Depois (Gold)':>22}")
    for nome, antes, depois in linhas:
        print(f"  {nome:<24}{antes:>22}{depois:>22}")
    print("\nPergunta para a turma: qual desses números você levaria para a diretoria?")


if __name__ == "__main__":
    main()
