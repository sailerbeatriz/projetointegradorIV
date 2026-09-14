"""
Etapa 3 — Avaliação retrospectiva do detector de anomalias.

O escore z já foi calculado na etapa 1. Aqui os picos reais de cada série são
identificados por proeminência e, para cada limiar candidato, mede-se:

  * cobertura .... proporção de picos precedidos por ao menos um alerta;
  * antecedência .. dias entre o primeiro alerta do episódio e o pico;
  * taxa de alerta  proporção de dias-município sinalizados — o custo do método.

Cobertura alta com taxa de alerta alta não é mérito: avisar todo dia "detecta"
tudo. As duas medidas só fazem sentido lidas juntas.

Uso:  python 03_avaliar_alerta.py
Saídas: dados/picos.parquet
        dados/desempenho_alerta.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import find_peaks

DADOS = Path(__file__).parent / "dados"
ENTRADA = DADOS / "serie_municipal.parquet"
PICOS = DADOS / "picos.parquet"
DESEMPENHO = DADOS / "desempenho_alerta.csv"

LIMIARES = [2.0, 2.5, 3.0, 3.5, 4.0]  # limiares de escore z avaliados
PISO_CASOS = 3.0      # média móvel mínima para que um alerta seja considerado
BUSCA_DIAS = 60       # janela de busca de alerta antes de cada pico
PROEMINENCIA = 0.20   # proeminência mínima do pico, como fração do máximo da série
ALTURA = 0.25         # altura mínima do pico, como fração do máximo da série


def identificar_picos(serie: pd.Series) -> pd.DatetimeIndex:
    """Picos relevantes da série, ignorando ondulações pequenas."""
    maximo = serie.max()
    if not np.isfinite(maximo) or maximo <= 0:
        return pd.DatetimeIndex([])
    idx, _ = find_peaks(
        serie.values,
        prominence=max(maximo * PROEMINENCIA, 3),
        height=max(maximo * ALTURA, 5),
    )
    return serie.index[idx]


def main() -> None:
    df = pd.read_parquet(ENTRADA).sort_values(["nome_munic", "datahora"])

    registros, dias_validos = [], 0
    alertas_por_limiar = {limiar: 0 for limiar in LIMIARES}

    for municipio, d in df.groupby("nome_munic", sort=False):
        serie = d.set_index("datahora")["casos_mm7d"]
        z = d.set_index("datahora")["z"]
        picos = identificar_picos(serie)
        dias_validos += int(z.notna().sum())

        for limiar in LIMIARES:
            alerta = (z >= limiar) & (serie >= PISO_CASOS)
            alertas_por_limiar[limiar] += int(alerta.sum())
            datas_alerta = z.index[alerta.fillna(False).values]
            for data_pico in picos:
                janela = datas_alerta[
                    (datas_alerta < data_pico)
                    & (datas_alerta >= data_pico - pd.Timedelta(days=BUSCA_DIAS))
                ]
                registros.append({
                    "municipio": municipio,
                    "limiar": limiar,
                    "pico": data_pico,
                    "alertado": len(janela) > 0,
                    "antecedencia": (data_pico - janela.min()).days if len(janela) else np.nan,
                })

    picos_df = pd.DataFrame(registros)
    picos_df.to_parquet(PICOS, compression="zstd", index=False)

    linhas = []
    for limiar in LIMIARES:
        sub = picos_df[picos_df["limiar"] == limiar]
        linhas.append({
            "limiar": limiar,
            "picos": len(sub),
            "cobertura": sub["alertado"].mean(),
            "antecedencia_mediana": sub["antecedencia"].median(),
            "antecedencia_q1": sub["antecedencia"].quantile(0.25),
            "antecedencia_q3": sub["antecedencia"].quantile(0.75),
            "taxa_alerta": alertas_por_limiar[limiar] / dias_validos,
        })
    desempenho = pd.DataFrame(linhas)
    desempenho.to_csv(DESEMPENHO, index=False)

    print(f"municípios .......... {df['nome_munic'].nunique()}")
    print(f"picos por limiar .... {len(picos_df) // len(LIMIARES)}")
    print("\ndesempenho por limiar de escore z:")
    print(
        desempenho.assign(
            cobertura=lambda t: (t["cobertura"] * 100).round(1).astype(str) + "%",
            taxa_alerta=lambda t: (t["taxa_alerta"] * 100).round(2).astype(str) + "%",
        )[["limiar", "picos", "cobertura", "antecedencia_mediana", "taxa_alerta"]].to_string(index=False)
    )
    print(f"\ngravado em {PICOS} e {DESEMPENHO}")


if __name__ == "__main__":
    main()
