# -*- coding: utf-8 -*-
"""
ETAPA 7 - QUALIDADE DE DADOS

Testes simples que todo pipeline deveria ter: contagem, chaves e valores.
As consultas usam SQL (DuckDB) direto sobre os arquivos Parquet das três camadas.
Se algum teste falhar, o script termina com erro, e o painel NÃO deveria ser atualizado.
"""
import sys

from config import conectar_duckdb, titulo

resultados = []


def checar(nome, condicao, detalhe=""):
    resultados.append(bool(condicao))
    print(f"  [{'OK' if condicao else 'FALHOU'}] {nome}" + (f"  ({detalhe})" if detalhe else ""))


def main():
    titulo("QUALIDADE DE DADOS")
    con = conectar_duckdb()

    def valor(sql):
        return con.execute(sql).fetchone()[0]

    print("\nContagem: nenhuma venda pode 'sumir' sem explicação")
    n_bronze = valor("SELECT COUNT(*) FROM (SELECT DISTINCT * FROM bronze_vendas)")
    n_silver = valor("SELECT COUNT(*) FROM silver_vendas")
    n_rej = valor("SELECT COUNT(*) FROM silver_vendas_rejeitadas")
    checar("Bronze sem duplicidades = Silver + rejeitadas", n_bronze == n_silver + n_rej,
           f"{n_bronze} = {n_silver} + {n_rej}")
    n_concl = valor("SELECT COUNT(*) FROM silver_vendas WHERE status = 'Concluída'")
    n_fato = valor("SELECT COUNT(*) FROM fato_vendas")
    checar("Vendas concluídas na Silver = linhas da fato", n_concl == n_fato, f"{n_concl} = {n_fato}")

    print("\nChaves: dimensões sem repetição e fato ligada às dimensões")
    for dim, sk in [("dim_cliente", "sk_cliente"), ("dim_produto", "sk_produto"), ("dim_calendario", "sk_data")]:
        rep = valor(f"SELECT COUNT(*) - COUNT(DISTINCT {sk}) FROM {dim}")
        checar(f"{dim}: chave única", rep == 0, f"{rep} repetidas")
    rep = valor("SELECT COUNT(*) - COUNT(DISTINCT id_venda) FROM fato_vendas")
    checar("fato_vendas: id_venda único", rep == 0, f"{rep} repetidos")

    # EXERCÍCIO 9: integridade referencial. Toda sk_produto da fato precisa existir na dim_produto.
    #   dica: LEFT JOIN da fato com a dimensão e conte onde a chave da dimensão ficou NULL
    orfas = valor("""SELECT COUNT(*) FROM fato_vendas f
                     LEFT JOIN dim_produto d ON d.sk_produto = f.sk_produto
                     WHERE d.sk_produto IS NULL""")
    checar("fato_vendas -> dim_produto sem órfãos", orfas == 0, f"{orfas} órfãs")
    orfas = valor("""SELECT COUNT(*) FROM fato_vendas f
                     LEFT JOIN dim_calendario d ON d.sk_data = f.sk_data WHERE d.sk_data IS NULL""")
    checar("fato_vendas -> dim_calendario sem órfãos", orfas == 0, f"{orfas} órfãs")

    print("\nValores: faixas que fazem sentido para o negócio")
    checar("Quantidade sempre maior que zero", valor("SELECT COUNT(*) FROM fato_vendas WHERE quantidade <= 0") == 0)
    checar("Valor líquido sem nulos ou negativos",
           valor("SELECT COUNT(*) FROM fato_vendas WHERE valor_liquido IS NULL OR valor_liquido < 0") == 0)
    checar("Desconto nunca maior que o valor bruto",
           valor("SELECT COUNT(*) FROM fato_vendas WHERE valor_desconto > valor_bruto") == 0)
    sem_cliente = valor("SELECT COUNT(*) FROM fato_vendas WHERE sk_cliente = 0")
    perc = 100 * sem_cliente / max(n_fato, 1)
    checar("Vendas sem cliente identificado abaixo de 2%", perc < 2, f"{sem_cliente} vendas, {perc:.1f}%")

    con.close()
    falhas = resultados.count(False)
    print(f"\n{len(resultados) - falhas} de {len(resultados)} testes aprovados.")
    if falhas:
        sys.exit(1)


if __name__ == "__main__":
    main()
