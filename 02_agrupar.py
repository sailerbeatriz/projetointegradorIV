"""
Etapa 2 — Engenharia de atributos e agrupamento dos municípios.

Constrói sete indicadores por município, todos normalizados pela população ou
adimensionais (nunca contagens brutas, que só refletiriam o porte), padroniza
por escore z e aplica k-médias para k de 2 a 8, avaliando cada partição pelo
coeficiente de silhueta.

Uso:  python 02_agrupar.py [k]
Saídas: dados/features_municipios.parquet
        dados/silhueta.csv
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

DADOS = Path(__file__).parent / "dados"
ENTRADA = DADOS / "serie_municipal.parquet"
DESTINO = DADOS / "features_municipios.parquet"
SILHUETA = DADOS / "silhueta.csv"

K_PADRAO = 4
FAIXA_K = range(2, 9)
SEMENTE = 42

ATRIBUTOS = [
    "Incidência/100 mil",
    "Mortalidade/100 mil",
    "Letalidade aparente",
    "Altura do pico/100 mil",
    "Variabilidade semanal",
    "Casos até 2021",
    "População (log)",
]


def construir_atributos(df: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por município, sete colunas comparáveis entre portes."""
    por_munic = df.groupby("nome_munic")
    ultimo = df[df["datahora"] == df["datahora"].max()].set_index("nome_munic")
    pop = ultimo["pop"]

    f = pd.DataFrame(index=ultimo.index)
    f["Incidência/100 mil"] = ultimo["casos"] / pop * 1e5
    f["Mortalidade/100 mil"] = ultimo["obitos"] / pop * 1e5
    f["Letalidade aparente"] = ultimo["obitos"] / ultimo["casos"] * 100
    f["Altura do pico/100 mil"] = por_munic["casos_mm7d"].max() / pop * 1e5
    # coeficiente de variação: dispersão relativa da série, adimensional
    f["Variabilidade semanal"] = (
        por_munic["casos_mm7d"].std() / por_munic["casos_mm7d"].mean().replace(0, np.nan)
    )
    # quando a epidemia se concentrou: proporção dos casos ocorridos até 2021
    ate_2021 = df[df["datahora"] < "2022-01-01"].groupby("nome_munic")["casos_novos"].sum()
    total = por_munic["casos_novos"].sum().replace(0, np.nan)
    f["Casos até 2021"] = (ate_2021 / total).reindex(f.index)
    f["População (log)"] = np.log10(pop)

    f["populacao"] = pop
    return f.dropna(subset=ATRIBUTOS)


def main() -> None:
    k_escolhido = int(sys.argv[1]) if len(sys.argv) > 1 else K_PADRAO

    df = pd.read_parquet(ENTRADA)
    f = construir_atributos(df)
    X = StandardScaler().fit_transform(f[ATRIBUTOS])

    linhas = []
    for k in FAIXA_K:
        rotulos = KMeans(n_clusters=k, n_init=10, random_state=SEMENTE).fit_predict(X)
        linhas.append({"k": k, "silhueta": silhouette_score(X, rotulos)})
    sil = pd.DataFrame(linhas)
    sil.to_csv(SILHUETA, index=False)

    f["grupo"] = KMeans(n_clusters=k_escolhido, n_init=10, random_state=SEMENTE).fit_predict(X) + 1
    # escores z guardados para o gráfico de perfil da interface
    for i, col in enumerate(ATRIBUTOS):
        f[f"z_{col}"] = X[:, i]
    f.reset_index().to_parquet(DESTINO, compression="zstd", index=False)

    print("coeficiente de silhueta por k:")
    for _, r in sil.iterrows():
        marca = "  <- máximo" if r["silhueta"] == sil["silhueta"].max() else ""
        print(f"   k={int(r['k'])}  {r['silhueta']:.3f}{marca}")
    print(f"\npartição adotada: k = {k_escolhido}")
    print(f"municípios por grupo: {f['grupo'].value_counts().sort_index().to_dict()}")
    print("\nperfil médio (valores brutos):")
    print(f.groupby("grupo")[ATRIBUTOS].mean().round(1).to_string())
    print(f"\ngravado em {DESTINO}")


if __name__ == "__main__":
    main()
