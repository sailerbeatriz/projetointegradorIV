"""
05_verificacoes.py — verificações de reprodutibilidade do PI IV.

Roda depois de 01_preparar_dados.py, 02_agrupar.py e 03_avaliar_alerta.py.
Não altera nenhum arquivo do projeto: só lê dados/ e imprime os números
usados no relatório, para que qualquer pessoa possa conferi-los.

Uso:
    python 05_verificacoes.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import find_peaks
from scipy.stats import spearmanr
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

DADOS = Path(__file__).parent / "dados"
SERIE = DADOS / "serie_municipal.parquet"

ATRIBUTOS = [
    "Incidência/100 mil", "Mortalidade/100 mil", "Letalidade aparente",
    "Altura do pico/100 mil", "Variabilidade semanal", "Casos até 2021",
    "População (log)",
]
LIMIARES = [2.0, 2.5, 3.0, 3.5, 4.0]
PISO_CASOS, BUSCA_DIAS, PROEMINENCIA, ALTURA = 3.0, 60, 0.20, 0.25


def titulo(t):
    print(f"\n{'=' * 70}\n{t}\n{'=' * 70}")


def base(df):
    """Confere o que a seção 2.5 afirma sobre a base tratada."""
    titulo("1. BASE TRATADA (Tabela 1 do relatório)")
    print(f"registros ................. {len(df):,}".replace(",", "."))
    print(f"municípios ................ {df['nome_munic'].nunique()}")
    print(f"datas distintas ........... {df['datahora'].nunique()}")
    print(f"período ................... {df['datahora'].min():%d/%m/%Y} a {df['datahora'].max():%d/%m/%Y}")
    ult = df[df.datahora == df.datahora.max()]
    print(f"casos acumulados .......... {int(ult['casos'].sum()):,}".replace(",", "."))
    print(f"óbitos acumulados ......... {int(ult['obitos'].sum()):,}".replace(",", "."))
    print(f"população de referência ... {int(ult['pop'].sum()):,}".replace(",", "."))
    print(f"variações negativas ....... casos: {(df.casos_novos < 0).sum()} | óbitos: {(df.obitos_novos < 0).sum()}")
    print("   (o relatório afirma que a base tratada não tem variações negativas)")


def media_movel(df, municipio="Bauru"):
    """A média móvel da Seade é retroativa ou centrada? (seção 2.4)"""
    titulo("2. TIPO DA MÉDIA MÓVEL (casos_mm7d)")
    g = df[df.nome_munic == municipio].set_index("datahora")
    cmp = pd.DataFrame({
        "seade": g["casos_mm7d"],
        "retroativa": g["casos_novos"].rolling(7).mean(),
        "centrada": g["casos_novos"].rolling(7, center=True).mean(),
    }).dropna()
    print(f"erro médio absoluto contra a média retroativa: {(cmp.seade - cmp.retroativa).abs().mean():.4f}")
    print(f"erro médio absoluto contra a média centrada .: {(cmp.seade - cmp.centrada).abs().mean():.4f}")
    print("   (erro zero indica qual das duas a Seade publica)")


def figura1(df):
    """Valores citados no parágrafo da Figura 1."""
    titulo("3. SÉRIE ESTADUAL (Figura 1)")
    est = df.groupby("datahora")[["casos_novos", "casos_mm7d"]].sum()
    print("maiores valores da média móvel somada:")
    print(est["casos_mm7d"].nlargest(5).round(0).to_string())
    print("\nsaltos de notificação citados no texto:")
    for dia in ("2021-09-16", "2021-12-30"):
        d = pd.Timestamp(dia)
        janela = est.loc[d - pd.Timedelta(days=6):d, "casos_novos"].astype(int)
        print(f"  {dia}: {int(est.loc[d, 'casos_novos'])} casos | semana anterior: "
              f"{janela.min()} a {janela.iloc[:-1].max()}")


def figura2(df):
    """Correlação citada no parágrafo da Figura 2."""
    titulo("4. INCIDÊNCIA × LETALIDADE (Figura 2)")
    ult = df[df.datahora == df.datahora.max()].set_index("nome_munic")
    inc = ult["casos"] / ult["pop"] * 1e5
    let = ult["obitos"] / ult["casos"] * 100
    ok = inc.notna() & let.notna()
    rho, p = spearmanr(inc[ok], let[ok])
    print(f"n = {int(ok.sum())}  |  Spearman rho = {rho:.3f}  |  p = {p:.2e}")
    print(f"mediana da incidência ..... {inc.median():,.0f} por 100 mil".replace(",", "."))
    print(f"mediana da letalidade ..... {let.median():.2f}%")


def agrupamento(df):
    """Refaz o script 02 e compara com o arquivo gravado."""
    titulo("5. AGRUPAMENTO (Figura 3, Figura 4 e Tabela 2)")
    por = df.groupby("nome_munic")
    ult = df[df.datahora == df.datahora.max()].set_index("nome_munic")
    pop = ult["pop"]
    f = pd.DataFrame(index=ult.index)
    f["Incidência/100 mil"] = ult["casos"] / pop * 1e5
    f["Mortalidade/100 mil"] = ult["obitos"] / pop * 1e5
    f["Letalidade aparente"] = ult["obitos"] / ult["casos"] * 100
    f["Altura do pico/100 mil"] = por["casos_mm7d"].max() / pop * 1e5
    f["Variabilidade semanal"] = por["casos_mm7d"].std() / por["casos_mm7d"].mean().replace(0, np.nan)
    ate = df[df.datahora < "2022-01-01"].groupby("nome_munic")["casos_novos"].sum()
    f["Casos até 2021"] = (ate / por["casos_novos"].sum().replace(0, np.nan)).reindex(f.index)
    f["População (log)"] = np.log10(pop)
    f["populacao"] = pop
    f = f.dropna(subset=ATRIBUTOS)

    X = StandardScaler().fit_transform(f[ATRIBUTOS])
    print("coeficiente de silhueta por k:")
    for k in range(2, 9):
        s = silhouette_score(X, KMeans(n_clusters=k, n_init=10, random_state=42).fit_predict(X))
        print(f"   k = {k}  {s:.3f}")

    f["grupo"] = KMeans(n_clusters=4, n_init=10, random_state=42).fit_predict(X) + 1
    tab = f.groupby("grupo").agg(
        municipios=("populacao", "size"), pop_mediana=("populacao", "median"),
        incidencia=("Incidência/100 mil", "mean"), letalidade=("Letalidade aparente", "mean"),
        pico=("Altura do pico/100 mil", "mean"), casos_ate_2021=("Casos até 2021", "mean"))
    print("\nperfil dos grupos (médias, população em mediana):")
    print(tab.round(2).to_string())

    gravado = DADOS / "features_municipios.parquet"
    if gravado.exists():
        ofi = pd.read_parquet(gravado).set_index("nome_munic")
        iguais = int((f["grupo"] == ofi["grupo"].reindex(f.index)).sum())
        print(f"\nmunicípios com o mesmo grupo do arquivo gravado: {iguais} de {len(f)}")


def alerta(df):
    """Refaz o script 03 e compara com desempenho_alerta.csv."""
    titulo("6. DESEMPENHO DO DETECTOR (Tabelas 3 e 4)")
    regs, dias, alertas = [], 0, {l: 0 for l in LIMIARES}
    for _, d in df.groupby("nome_munic", sort=False):
        serie = d.set_index("datahora")["casos_mm7d"]
        z = d.set_index("datahora")["z"]
        maximo = serie.max()
        if not np.isfinite(maximo) or maximo <= 0:
            continue
        idx, _ = find_peaks(serie.values, prominence=max(maximo * PROEMINENCIA, 3),
                            height=max(maximo * ALTURA, 5))
        picos = serie.index[idx]
        dias += int(z.notna().sum())
        for limiar in LIMIARES:
            al = (z >= limiar) & (serie >= PISO_CASOS)
            alertas[limiar] += int(al.sum())
            datas = z.index[al.fillna(False).values]
            for pico in picos:
                j = datas[(datas < pico) & (datas >= pico - pd.Timedelta(days=BUSCA_DIAS))]
                regs.append({"limiar": limiar, "alertado": len(j) > 0,
                             "antec": (pico - j.min()).days if len(j) else np.nan})
    r = pd.DataFrame(regs)
    linhas = []
    for limiar in LIMIARES:
        s = r[r.limiar == limiar]
        linhas.append({"limiar": limiar, "picos": len(s),
                       "cobertura_%": round(s.alertado.mean() * 100, 2),
                       "antec_mediana": s.antec.median(),
                       "q1": s.antec.quantile(0.25), "q3": s.antec.quantile(0.75),
                       "taxa_alerta_%": round(alertas[limiar] / dias * 100, 2)})
    print(pd.DataFrame(linhas).to_string(index=False))
    print(f"\ndias-município com escore z válido: {dias:,}".replace(",", "."))


def lacunas(df, minimo=7):
    """Quantos alertas aparecem logo depois de uma interrupção de notificação."""
    titulo("7. FALHAS DE NOTIFICAÇÃO (limitação da seção 2.5)")
    df = df.copy()
    df["alerta"] = (df.z >= 3) & (df.casos_mm7d >= PISO_CASOS)
    achados = []
    for munic, g in df.groupby("nome_munic", sort=False):
        g = g.reset_index(drop=True)
        zeros = (g.casos_novos == 0).astype(int)
        blocos = (zeros != zeros.shift()).cumsum()
        for _, run in g[zeros == 1].groupby(blocos[zeros == 1]):
            if len(run) >= minimo:
                i = run.index[-1]
                depois = g.loc[i + 1:i + 7]
                if len(depois):
                    achados.append({"municipio": munic, "dias_em_zero": len(run),
                                    "alertas_7d": int(depois.alerta.sum())})
    a = pd.DataFrame(achados)
    print(f"sequências de {minimo} dias ou mais em zero ... {len(a)} em {a.municipio.nunique()} municípios")
    print(f"seguidas de alerta em até 7 dias ........... {int((a.alertas_7d > 0).sum())}")
    print(f"alertas nessas janelas .................... {int(a.alertas_7d.sum())} "
          f"({a.alertas_7d.sum() / df.alerta.sum() * 100:.1f}% do total de alertas)")


def main():
    df = pd.read_parquet(SERIE).sort_values(["nome_munic", "datahora"])
    base(df)
    media_movel(df)
    figura1(df)
    figura2(df)
    agrupamento(df)
    alerta(df)
    lacunas(df)
    print("\nFim das verificações.")


if __name__ == "__main__":
    main()
