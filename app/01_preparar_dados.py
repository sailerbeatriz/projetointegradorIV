"""
Etapa 1 — Preparação da base municipal de COVID-19 do Estado de São Paulo.

Lê o arquivo dados_covid_sp.csv (Fundação Seade), aplica o pré-processamento
descrito na seção 2.4 do relatório e grava a base de trabalho em formato
colunar comprimido.

Também calcula, para cada município e cada data, o escore z da média móvel de
7 dias em relação a uma janela de referência recente. É esse escore que o
aplicativo usa para disparar alertas: o limiar fica ajustável na interface,
sem precisar recalcular nada.

Uso:  python 01_preparar_dados.py
Saída: dados/serie_municipal.parquet
"""

import urllib.request
from pathlib import Path

import pandas as pd

URL = "https://raw.githubusercontent.com/seade-R/dados-covid-sp/master/data/dados_covid_sp.csv"

DADOS = Path(__file__).parent / "dados"
ORIGEM = DADOS / "dados_covid_sp.csv"
DESTINO = DADOS / "serie_municipal.parquet"

# Parâmetros da janela de referência do detector de anomalias (seção 2.4).
JANELA_REF = 28   # dias usados para estimar o comportamento esperado
DEFASAGEM = 7     # dias de afastamento entre a janela e a data avaliada
PISO_SD = 0.5     # piso do desvio-padrão, evita divisão por valores ~0


def baixar_se_preciso() -> Path:
    """Baixa o CSV da Fundação Seade apenas na primeira execução."""
    DADOS.mkdir(exist_ok=True)
    if not ORIGEM.exists():
        print("Baixando a base do repositório da Fundação Seade (~77 MB)...")
        urllib.request.urlretrieve(URL, ORIGEM)
    return ORIGEM


def main() -> None:
    caminho = baixar_se_preciso()

    # O arquivo é brasileiro: ponto e vírgula separa campos, vírgula separa decimais.
    df = pd.read_csv(
        caminho,
        sep=";",
        decimal=",",
        dtype={"codigo_ibge": str},
        parse_dates=["datahora"],
    )
    registros_originais = len(df)

    # Auditoria das variações diárias negativas ANTES de qualquer filtro.
    # Elas decorrem de retificações retroativas: quando a fonte reclassifica um
    # caso antes sem município, a categoria residual é descontada e fica
    # negativa. Por isso concentram-se inteiramente em "Ignorado".
    neg_casos = int((df["casos_novos"] < 0).sum())
    neg_obitos = int((df["obitos_novos"] < 0).sum())
    ignorado = df["nome_munic"] == "Ignorado"
    neg_fora = int(((df["casos_novos"] < 0) & ~ignorado).sum()
                   + ((df["obitos_novos"] < 0) & ~ignorado).sum())

    # "Ignorado" é uma categoria residual, sem município e sem população de
    # referência. Não serve para indicadores normalizados, então sai da base.
    df = df[~ignorado].copy()

    df = df.sort_values(["nome_munic", "datahora"]).reset_index(drop=True)

    # --- escore z da média móvel em relação à janela de referência ----------
    # A janela termina DEFASAGEM dias antes da data avaliada, para que o
    # próprio início da subida não contamine o valor esperado.
    referencia = df.groupby("nome_munic")["casos_mm7d"].shift(DEFASAGEM)
    df["_ref"] = referencia
    por_munic = df.groupby("nome_munic")["_ref"]
    media = por_munic.transform(lambda s: s.rolling(JANELA_REF).mean())
    desvio = por_munic.transform(lambda s: s.rolling(JANELA_REF).std())
    df["z"] = ((df["casos_mm7d"] - media) / desvio.clip(lower=PISO_SD)).astype("float32")
    df = df.drop(columns="_ref")

    df.to_parquet(DESTINO, compression="zstd", index=False)

    mb_csv = caminho.stat().st_size / 1e6
    mb_pq = DESTINO.stat().st_size / 1e6
    print(f"registros originais ......... {registros_originais:,}".replace(",", "."))
    print(f"registros após a limpeza .... {len(df):,}".replace(",", "."))
    print(f"municípios .................. {df['nome_munic'].nunique()}")
    print(f"datas ....................... {df['datahora'].nunique()}")
    print(f"período ..................... {df['datahora'].min():%d/%m/%Y} a {df['datahora'].max():%d/%m/%Y}")
    print(f"variações negativas ......... {neg_casos} em casos e {neg_obitos} em óbitos;")
    print(f"                              {neg_fora} fora da categoria residual 'Ignorado'")
    print(f"tamanho ..................... {mb_csv:.1f} MB em CSV -> {mb_pq:.1f} MB em Parquet")
    print(f"gravado em .................. {DESTINO}")


if __name__ == "__main__":
    main()
