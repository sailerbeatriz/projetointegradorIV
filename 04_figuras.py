"""
04_figuras.py — gera as cinco figuras do relatório a partir dos dados tratados.

Roda depois de 01_preparar_dados.py, 02_agrupar.py e 03_avaliar_alerta.py.
Grava PNGs de 300 dpi em figuras/, prontos para inserir no documento.

Uso:
    python 04_figuras.py

Saídas:
    figuras/figura1_serie_estadual.png
    figuras/figura2_incidencia_letalidade.png
    figuras/figura3_silhueta.png
    figuras/figura4_perfil_grupos.png
    figuras/figura5_bauru.png
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter

BASE = Path(__file__).parent
DADOS = BASE / "dados"
FIGURAS = BASE / "figuras"
FIGURAS.mkdir(exist_ok=True)

MUNICIPIO_EXEMPLO = "Bauru"
LIMIAR = 3.0
PISO_CASOS = 3.0

# Paleta do projeto, validada para daltonismo (separação perceptual ΔE ≥ 8).
AZUL, TERRACOTA, VERDE, TINTA = "#4a7fb5", "#d97757", "#3fa78a", "#1f2a26"
DPI = 300

plt.rcParams.update({
    "figure.dpi": DPI, "savefig.dpi": DPI, "savefig.bbox": "tight",
    "font.size": 9, "axes.titlesize": 9, "axes.labelsize": 9,
    "axes.edgecolor": "#b9c2bf", "axes.labelcolor": TINTA,
    "text.color": TINTA, "xtick.color": TINTA, "ytick.color": TINTA,
    "axes.spines.top": False, "axes.spines.right": False,
    "grid.color": "#e3e8e6", "grid.linewidth": 0.8,
    "figure.facecolor": "white", "axes.facecolor": "white",
})


def br(valor, casas=0):
    """Formata número no padrão brasileiro: ponto de milhar, vírgula decimal."""
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "§").replace(".", ",").replace("§", ".")


def eixo_br(casas=0):
    return FuncFormatter(lambda v, _: br(v, casas))


def serie_estadual(df):
    """Figura 1 — novos casos diários no Estado, média móvel de 7 dias."""
    est = df.groupby("datahora")["casos_mm7d"].sum()
    pico_data, pico_valor = est.idxmax(), est.max()

    fig, ax = plt.subplots(figsize=(6.19, 3.0))
    ax.fill_between(est.index, est.values, color=AZUL, alpha=0.15, linewidth=0)
    ax.plot(est.index, est.values, color=AZUL, linewidth=1.6)
    ax.annotate(f"pico: {br(pico_valor)}\n{pico_data:%d/%m/%Y}",
                xy=(pico_data, pico_valor), xycoords="data",
                xytext=(0.06, 0.88), textcoords="axes fraction", fontsize=8,
                va="top", ha="left",
                arrowprops=dict(arrowstyle="-", color="#7d8a86", linewidth=0.8,
                                shrinkA=2, shrinkB=3))
    ax.set_ylabel("Novos casos por dia (média móvel de 7 dias)")
    ax.yaxis.set_major_formatter(eixo_br())
    ax.set_ylim(bottom=0)
    ax.grid(axis="y")
    ax.set_axisbelow(True)
    fig.savefig(FIGURAS / "figura1_serie_estadual.png")
    plt.close(fig)
    return f"Figura 1: pico de {br(pico_valor)} em {pico_data:%d/%m/%Y}"


def incidencia_letalidade(df):
    """Figura 2 — incidência acumulada × letalidade aparente, um ponto por município."""
    ult = df[df.datahora == df.datahora.max()].set_index("nome_munic")
    inc = ult["casos"] / ult["pop"] * 1e5
    let = ult["obitos"] / ult["casos"] * 100
    ok = inc.notna() & let.notna()
    inc, let = inc[ok], let[ok]

    fig, ax = plt.subplots(figsize=(6.2, 3.3))
    ax.scatter(inc, let, s=22, color=AZUL, alpha=0.45, linewidths=0)
    ax.axvline(inc.median(), color="#7d8a86", linestyle="--", linewidth=0.9)
    ax.axhline(let.median(), color="#7d8a86", linestyle="--", linewidth=0.9)
    ax.annotate(f"mediana: {br(inc.median())}", xy=(inc.median(), ax.get_ylim()[1]),
                xytext=(6, -12), textcoords="offset points", fontsize=8)
    ax.annotate(f"mediana: {br(let.median(), 2)}%", xy=(ax.get_xlim()[1], let.median()),
                xytext=(-92, 6), textcoords="offset points", fontsize=8)
    ax.set_xlabel("Incidência acumulada (casos por 100 mil habitantes)")
    ax.set_ylabel("Letalidade aparente (%)")
    ax.xaxis.set_major_formatter(eixo_br())
    ax.yaxis.set_major_formatter(eixo_br())
    ax.grid(axis="both")
    ax.set_axisbelow(True)
    fig.savefig(FIGURAS / "figura2_incidencia_letalidade.png")
    plt.close(fig)
    return (f"Figura 2: n = {len(inc)}, medianas {br(inc.median())} e "
            f"{br(let.median(), 2)}%")


def silhueta():
    """Figura 3 — coeficiente de silhueta por número de agrupamentos."""
    sil = pd.read_csv(DADOS / "silhueta.csv")
    melhor = sil.loc[sil.silhueta.idxmax()]

    fig, ax = plt.subplots(figsize=(5.5, 2.7))
    ax.plot(sil.k, sil.silhueta, color=AZUL, linewidth=1.8, marker="o", markersize=5)
    ax.scatter([melhor.k], [melhor.silhueta], s=150, facecolors="none",
               edgecolors=TERRACOTA, linewidths=1.8)
    ax.annotate(f"máximo: k = {int(melhor.k)}\n{br(melhor.silhueta, 3)}",
                xy=(melhor.k, melhor.silhueta), xytext=(12, -6),
                textcoords="offset points", fontsize=8)
    ax.set_xlabel("Número de agrupamentos (k)")
    ax.set_ylabel("Coeficiente de silhueta")
    ax.yaxis.set_major_formatter(eixo_br(2))
    ax.grid(axis="y")
    ax.set_axisbelow(True)
    fig.savefig(FIGURAS / "figura3_silhueta.png")
    plt.close(fig)
    return f"Figura 3: máximo em k = {int(melhor.k)} ({br(melhor.silhueta, 3)})"


def perfil_grupos():
    """Figura 4 — perfil padronizado dos grupos (escore z médio por atributo)."""
    f = pd.read_parquet(DADOS / "features_municipios.parquet")
    colunas = [c for c in f.columns if c.startswith("z_")]
    rotulos = ["Incidência/100 mil", "Mortalidade/100 mil", "Letalidade aparente",
               "Altura do pico/100 mil", "Variabilidade da série", "Casos até 2021",
               "População (log)"]
    perfil = f.groupby("grupo")[colunas].mean()
    tamanhos = f.groupby("grupo").size()

    # Diverging: dois matizes da paleta do projeto com ponto neutro claro no meio.
    cmap = LinearSegmentedColormap.from_list("azul_terracota", [AZUL, "#f2f4f3", TERRACOTA])
    limite = float(np.abs(perfil.values).max())

    fig, ax = plt.subplots(figsize=(5.96, 2.83))
    im = ax.imshow(perfil.values, cmap=cmap, vmin=-limite, vmax=limite, aspect="auto")
    ax.set_xticks(range(len(rotulos)))
    ax.set_xticklabels(rotulos, rotation=32, ha="right", fontsize=8)
    ax.set_yticks(range(len(perfil)))
    ax.set_yticklabels([f"Grupo {g}  (n={tamanhos[g]})" for g in perfil.index], fontsize=8)
    for i in range(perfil.shape[0]):
        for j in range(perfil.shape[1]):
            v = perfil.values[i, j]
            ax.text(j, i, br(v, 1) if abs(v) >= 0.05 else "0,0", ha="center", va="center",
                    fontsize=8, color="white" if abs(v) > limite * 0.62 else TINTA)
    for eixo in ("top", "right", "left", "bottom"):
        ax.spines[eixo].set_visible(False)
    ax.tick_params(length=0)
    barra = fig.colorbar(im, ax=ax, shrink=0.85, pad=0.02)
    barra.set_label("escore z", fontsize=8)
    barra.ax.tick_params(labelsize=8)
    barra.ax.yaxis.set_major_formatter(eixo_br(0))
    fig.savefig(FIGURAS / "figura4_perfil_grupos.png")
    plt.close(fig)
    return "Figura 4: " + ", ".join(f"grupo {g} n={tamanhos[g]}" for g in perfil.index)


def exemplo_municipio(df, municipio=MUNICIPIO_EXEMPLO):
    """Figura 5 — série, alertas e picos de um município."""
    from scipy.signal import find_peaks

    d = df[df.nome_munic == municipio].set_index("datahora")
    serie, z = d["casos_mm7d"], d["z"]
    maximo = serie.max()
    idx, _ = find_peaks(serie.values, prominence=max(maximo * 0.20, 3),
                        height=max(maximo * 0.25, 5))
    picos = serie.index[idx]
    alerta = (z >= LIMIAR) & (serie >= PISO_CASOS)
    datas_alerta = z.index[alerta.fillna(False).values]

    fig, ax = plt.subplots(figsize=(6.19, 3.0))
    for dia in datas_alerta:
        ax.axvspan(dia - pd.Timedelta(days=1), dia + pd.Timedelta(days=1),
                   color=TERRACOTA, alpha=0.35, linewidth=0)
    ax.plot(serie.index, serie.values, color=AZUL, linewidth=1.6, label="casos (média móvel de 7 dias)")
    ax.scatter(picos, serie.loc[picos], s=42, facecolors="none", edgecolors=TINTA,
               linewidths=1.2, label="pico identificado", zorder=3)
    faixa = Patch(facecolor=TERRACOTA, alpha=0.35, label="dia com alerta disparado")
    ax.set_ylabel(f"Novos casos por dia — {municipio}")
    ax.yaxis.set_major_formatter(eixo_br())
    ax.set_ylim(bottom=0)
    ax.grid(axis="y")
    ax.set_axisbelow(True)
    alcas, rotulos_legenda = ax.get_legend_handles_labels()
    ax.legend(alcas + [faixa], rotulos_legenda + [faixa.get_label()],
              loc="upper left", frameon=False, fontsize=8)
    fig.savefig(FIGURAS / "figura5_bauru.png")
    plt.close(fig)
    return (f"Figura 5 ({municipio}): {len(picos)} picos, {int(alerta.sum())} dias com alerta")


def main():
    df = pd.read_parquet(DADOS / "serie_municipal.parquet").sort_values(["nome_munic", "datahora"])
    for linha in (serie_estadual(df), incidencia_letalidade(df), silhueta(),
                  perfil_grupos(), exemplo_municipio(df)):
        print(linha)
    print(f"\nfiguras gravadas em {FIGURAS}")


if __name__ == "__main__":
    main()
