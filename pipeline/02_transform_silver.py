# -*- coding: utf-8 -*-
"""
ETAPA 5 - TRANSFORM (camada Silver)

Aqui o dado bruto vira dado confiável:
  tipagem, datas inválidas, nulos, duplicidades, padronização e regras de negócio.
Registros que não podem ser corrigidos NÃO são apagados em silêncio:
vão para a tabela vendas_rejeitadas, com o motivo.

Saída: dados/silver/*.parquet, agora com os tipos corretos (data, número, texto).
"""
import unicodedata

import pandas as pd

from config import CAMADAS, gravar, ler, titulo


# ------------------------------------------------------------------ funções de apoio
def ler_bronze(tabela):
    return ler("bronze", tabela).drop(columns=["_origem", "_data_carga"])


def chave(texto):
    """'  Maringá ' -> 'maringa': minúsculas, sem acento e sem espaços extras. Serve para COMPARAR textos."""
    if texto is None or pd.isna(texto):
        return ""
    t = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return " ".join(t.lower().split())


def limpar_texto(serie):
    """Remove espaços no início, no fim e espaços duplicados."""
    return serie.astype("string").str.strip().str.replace(r"\s+", " ", regex=True)


def converter_data(serie):
    """Aceita '2025-03-15' e '15/03/2025'. O que não for uma data válida vira NaT (vazio)."""
    s = serie.astype("string").str.strip()
    # EXERCÍCIO 2: converta os dois formatos e junte os resultados
    #   dica: errors="coerce" transforma o que não é data válida em NaT, sem quebrar o código
    iso = pd.to_datetime(s, format="%Y-%m-%d", errors="coerce")
    br = pd.to_datetime(s, format="%d/%m/%Y", errors="coerce")
    return iso.fillna(br)


def converter_numero(serie):
    """'1.299,90' -> 1299.9 | '1299.90' -> 1299.9 | '10%' -> 10 | '2 un' -> 2 | '' -> NaN"""
    s = serie.astype("string").str.strip()
    formato_br = s.str.contains(",", na=False)
    # EXERCÍCIO 3: no formato brasileiro, tire o ponto de milhar e troque a vírgula decimal por ponto
    s = s.where(~formato_br, s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False))
    s = s.str.replace(r"[^0-9.\-]", "", regex=True)            # remove 'un', '%', espaços...
    return pd.to_numeric(s.astype(object), errors="coerce").astype("float64")


# ------------------------------------------------------------------ dicionários de padronização
CIDADES = ["Toledo", "Cascavel", "Umuarama", "Maringá", "Curitiba", "Londrina", "Foz do Iguaçu",
           "Francisco Beltrão", "Guaíra", "Paranavaí", "Marechal Cândido Rondon"]
MAPA_CIDADE = {chave(c): c for c in CIDADES} | {"mal. candido rondon": "Marechal Cândido Rondon"}

MAPA_CANAL = {"loja fisica": "Loja Física", "loja": "Loja Física",
              "e-commerce": "E-commerce", "ecommerce": "E-commerce", "site": "E-commerce",
              "app": "App", "aplicativo": "App"}

MAPA_CATEGORIA = {chave(c): c for c in ["Informática", "Celulares", "Áudio", "Eletrodomésticos", "Games", "TV e Vídeo"]}
MAPA_CATEGORIA["celular"] = "Celulares"

MAPA_SEGMENTO = {"pessoa fisica": "Pessoa Física", "pf": "Pessoa Física",
                 "pessoa juridica": "Pessoa Jurídica", "pj": "Pessoa Jurídica"}

MAPA_STATUS = {"concluida": "Concluída", "cancelada": "Cancelada"}


# ------------------------------------------------------------------ tratamento por tabela
def tratar_produtos():
    df = ler_bronze("produtos")
    df["descricao"] = limpar_texto(df["descricao"])
    df["categoria"] = df["categoria"].map(chave).map(MAPA_CATEGORIA)
    df["preco_venda"] = converter_numero(df["preco_venda"])
    df["preco_custo"] = converter_numero(df["preco_custo"])
    df["ativo"] = df["ativo"].map(chave).map({"s": "S", "sim": "S", "n": "N", "nao": "N"})
    return df.drop_duplicates(subset="id_produto", keep="first")


def tratar_clientes():
    df = ler_bronze("clientes")
    df["nome"] = limpar_texto(df["nome"]).str.title()
    df["email"] = limpar_texto(df["email"]).str.lower()
    df["cidade"] = df["cidade"].map(chave).map(MAPA_CIDADE).fillna("Não informada")
    df["uf"] = df["uf"].map(chave).str.upper().replace("", "PR")
    df["segmento"] = df["segmento"].map(chave).map(MAPA_SEGMENTO)
    df["data_cadastro"] = converter_data(df["data_cadastro"])
    # O CRM exporta o histórico: o mesmo cliente pode aparecer mais de uma vez.
    # Mantemos o último registro (o mais atualizado).
    return df.drop_duplicates(subset="id_cliente", keep="last")


def tratar_vendas(produtos):
    df = ler_bronze("vendas")
    linhas_bronze = len(df)

    # EXERCÍCIO 4: remova as linhas duplicadas (exportação repetida do ERP)
    df = df.drop_duplicates()
    duplicadas = linhas_bronze - len(df)

    df["data_venda"] = converter_data(df["data_venda"])
    df["quantidade"] = converter_numero(df["quantidade"])
    df["valor_unitario"] = converter_numero(df["valor_unitario"])
    df["desconto_pct"] = converter_numero(df["desconto_pct"]).fillna(0)
    df["id_cliente"] = limpar_texto(df["id_cliente"]).fillna("")
    df["status"] = df["status"].map(chave).map(MAPA_STATUS)

    # EXERCÍCIO 5: padronize o canal usando a função chave() e o dicionário MAPA_CANAL
    df["canal"] = df["canal"].map(chave).map(MAPA_CANAL)

    # Regra de negócio: preço vazio na venda -> usa o preço de tabela do produto
    preco_tabela = produtos.set_index("id_produto")["preco_venda"]
    df["valor_unitario"] = df["valor_unitario"].fillna(df["id_produto"].map(preco_tabela))

    # Quarentena: o que não dá para corrigir vai para vendas_rejeitadas, com o motivo
    motivo = pd.Series("", index=df.index)
    motivo[df["data_venda"].isna()] = "data inválida ou vazia"
    motivo[(motivo == "") & ~(df["quantidade"] > 0)] = "quantidade inválida"
    rejeitadas = df[motivo != ""].assign(motivo=motivo[motivo != ""])
    df = df[motivo == ""].copy()

    # EXERCÍCIO 6: calcule os valores da venda
    #   valor_bruto    = quantidade x valor_unitario
    #   valor_desconto = valor_bruto x desconto_pct / 100
    #   valor_liquido  = valor_bruto - valor_desconto
    df["valor_bruto"] = (df["quantidade"] * df["valor_unitario"]).round(2)
    df["valor_desconto"] = (df["valor_bruto"] * df["desconto_pct"] / 100).round(2)
    df["valor_liquido"] = (df["valor_bruto"] - df["valor_desconto"]).round(2)

    df["quantidade"] = df["quantidade"].astype("int64")
    return df, rejeitadas, linhas_bronze, duplicadas


def tratar_metas():
    df = ler_bronze("metas")
    df["data_mes"] = pd.to_datetime("01/" + df["mes"].astype("string"), format="%d/%m/%Y")
    df["canal"] = df["canal"].map(chave).map(MAPA_CANAL)
    df["meta_faturamento"] = converter_numero(df["meta_faturamento"])
    return df[["data_mes", "canal", "meta_faturamento"]]


def main():
    titulo("TRANSFORM -> Silver (Parquet)")
    produtos = tratar_produtos()
    clientes = tratar_clientes()
    vendas, rejeitadas, bronze, duplicadas = tratar_vendas(produtos)
    metas = tratar_metas()

    for nome, df in [("produtos", produtos), ("clientes", clientes), ("vendas", vendas),
                     ("vendas_rejeitadas", rejeitadas), ("metas", metas)]:
        gravar(df, "silver", nome)
        print(f"  {nome:<18} {len(df):>6} linhas")

    print(f"\n  Vendas na Bronze ......... {bronze}")
    print(f"  Duplicadas removidas ..... {duplicadas}")
    print(f"  Enviadas à quarentena .... {len(rejeitadas)}")
    print(f"  Vendas válidas na Silver . {len(vendas)}")
    print(f"\nArquivos gerados em: {CAMADAS['silver']}")


if __name__ == "__main__":
    main()
