"""
Painel COVID-19 — Estado de São Paulo
Projeto Integrador em Computação IV (PJI410) — Univesp

Interface interativa sobre a série municipal da Fundação Seade, com duas
camadas de aprendizado de máquina: o agrupamento dos municípios por perfil de
disseminação e o alerta precoce por detecção de anomalias.

Antes de executar, rode na ordem:
    python 01_preparar_dados.py
    python 02_agrupar.py
    python 03_avaliar_alerta.py

Para executar:
    streamlit run app.py
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

DADOS = Path(__file__).parent / "dados"

# Paleta única do painel. Verde para o dado, terracota para o alerta — a cor de
# estado nunca é reaproveitada como cor de série. O par verde/terracota é
# oposto no círculo cromático e continua distinguível no daltonismo mais
# comum, ao contrário do par verde/vermelho.
VERDE, TERRACOTA, AZUL = "#3fa78a", "#d97757", "#4a7fb5"
CINZA, TINTA, TINTA2 = "#dfe6e2", "#1f2a26", "#5a6661"
VERDE_SUAVE = "rgba(63,167,138,0.14)"
# Sequência categórica: os três primeiros matizes são os validados para uso
# simultâneo; os demais só entram quando há legenda e rótulo direto.
CORES_GRUPO = [VERDE, TERRACOTA, AZUL, "#8a5fa8", "#b07c2a", "#2f6f5e", "#b5485d", "#7a8b99"]

FONTE = "IBM Plex Sans"

st.set_page_config(page_title="COVID-19 SP — Painel Analítico", page_icon="📈", layout="wide")

# IBM Plex Sans para toda a interface: títulos, widgets, tabelas e gráficos.
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');
    html, body, [class*="st-"], [data-testid="stAppViewContainer"],
    [data-testid="stSidebar"], .stMarkdown, .stMetric, button, input, select, textarea {
        font-family: 'IBM Plex Sans', system-ui, sans-serif !important;
    }
    h1, h2, h3, h4 { font-family: 'IBM Plex Sans', system-ui, sans-serif !important;
                     letter-spacing: -0.01em; }
    /* Os ícones do Streamlit são ligaduras de uma fonte própria: se herdarem a
       fonte do texto, aparecem como o nome do ícone escrito por extenso. */
    [data-testid="stIconMaterial"], .material-icons, .material-icons-rounded,
    .material-symbols-rounded, .material-symbols-outlined, span[class*="material-"] {
        font-family: 'Material Symbols Rounded', 'Material Icons Rounded',
                     'Material Symbols Outlined', 'Material Icons' !important;
    }
    [data-testid="stMetricValue"] { font-variant-numeric: tabular-nums; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ────────────────────────────── dados ──────────────────────────────
@st.cache_data
def carregar_serie() -> pd.DataFrame:
    return pd.read_parquet(DADOS / "serie_municipal.parquet")


@st.cache_data
def carregar_municipios() -> pd.DataFrame:
    return pd.read_parquet(DADOS / "features_municipios.parquet")


@st.cache_data
def carregar_silhueta() -> pd.DataFrame:
    return pd.read_csv(DADOS / "silhueta.csv")


@st.cache_data
def carregar_desempenho() -> pd.DataFrame:
    return pd.read_csv(DADOS / "desempenho_alerta.csv")


@st.cache_data
def carregar_picos() -> pd.DataFrame:
    return pd.read_parquet(DADOS / "picos.parquet")


try:
    serie = carregar_serie()
    municipios = carregar_municipios()
    silhueta = carregar_silhueta()
    desempenho = carregar_desempenho()
    picos = carregar_picos()
except FileNotFoundError as erro:
    st.error(
        f"Arquivo de dados não encontrado: {erro}\n\n"
        "Execute, nesta ordem, os scripts 01_preparar_dados.py, 02_agrupar.py "
        "e 03_avaliar_alerta.py antes de abrir o painel."
    )
    st.stop()

LISTA_MUNIC = sorted(serie["nome_munic"].unique())
DATA_MIN, DATA_MAX = serie["datahora"].min(), serie["datahora"].max()
ATRIBUTOS = [c[2:] for c in municipios.columns if c.startswith("z_")]

DESCRICAO_GRUPOS = {
    g: f"{len(d)} municípios · população mediana de {d['populacao'].median():,.0f} hab."
    .replace(",", ".")
    for g, d in municipios.groupby("grupo")
}


def eixo_limpo(fig, titulo_y: str = "") -> go.Figure:
    """Grade discreta, sem moldura, rótulos no tom do texto."""
    fig.update_layout(
        template="simple_white",
        margin=dict(l=10, r=10, t=30, b=10),
        height=380,
        hovermode="x unified",
        font=dict(color=TINTA, size=13, family=FONTE),
        yaxis_title=titulo_y,
        xaxis_title="",
    )
    fig.update_yaxes(gridcolor=CINZA, zeroline=False)
    fig.update_xaxes(gridcolor=CINZA)
    return fig


# ────────────────────────────── navegação ──────────────────────────────
st.sidebar.title("COVID-19 · São Paulo")
st.sidebar.caption("Projeto Integrador IV — Univesp")
pagina = st.sidebar.radio(
    "Seções",
    ["Visão geral", "Município", "Agrupamento", "Alerta precoce", "Comparativo"],
)
st.sidebar.divider()
st.sidebar.caption(
    f"Série de {DATA_MIN:%d/%m/%Y} a {DATA_MAX:%d/%m/%Y} · "
    f"{len(serie):,} registros · {len(LISTA_MUNIC)} municípios".replace(",", ".")
)
st.sidebar.caption("Fonte: Fundação Seade / Secretaria de Estado da Saúde de São Paulo.")


# ══════════════════════════════ VISÃO GERAL ══════════════════════════════
if pagina == "Visão geral":
    st.title("Visão geral do Estado")

    c1, c2 = st.columns([3, 1])
    with c1:
        periodo = st.slider(
            "Período",
            min_value=DATA_MIN.to_pydatetime(),
            max_value=DATA_MAX.to_pydatetime(),
            value=(DATA_MIN.to_pydatetime(), DATA_MAX.to_pydatetime()),
            format="DD/MM/YYYY",
        )
    with c2:
        metrica = st.selectbox("Métrica", ["Casos", "Óbitos"])

    coluna = "casos_mm7d" if metrica == "Casos" else "obitos_mm7d"
    recorte = serie[(serie["datahora"] >= periodo[0]) & (serie["datahora"] <= periodo[1])]
    estado = recorte.groupby("datahora", as_index=False)[coluna].sum()

    ultimo = serie[serie["datahora"] == DATA_MAX]
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Casos acumulados", f"{int(ultimo['casos'].sum()):,}".replace(",", "."))
    k2.metric("Óbitos acumulados", f"{int(ultimo['obitos'].sum()):,}".replace(",", "."))
    k3.metric("Letalidade aparente", f"{ultimo['obitos'].sum() / ultimo['casos'].sum() * 100:.2f}%")
    k4.metric("População coberta", f"{int(ultimo['pop'].sum()):,}".replace(",", "."))

    fig = px.area(estado, x="datahora", y=coluna, color_discrete_sequence=[VERDE])
    fig.update_traces(line=dict(width=2), fillcolor=VERDE_SUAVE)
    st.plotly_chart(eixo_limpo(fig, f"Novos {metrica.lower()} por dia (média móvel de 7 dias)"),
                    width="stretch")

    pico = estado.loc[estado[coluna].idxmax()]
    st.caption(
        f"Pico do período: {pico[coluna]:,.0f} {metrica.lower()} por dia em "
        f"{pico['datahora']:%d/%m/%Y}.".replace(",", ".")
    )


# ══════════════════════════════ MUNICÍPIO ══════════════════════════════
elif pagina == "Município":
    st.title("Série de um município")

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        alvo = st.selectbox("Município", LISTA_MUNIC, index=LISTA_MUNIC.index("Bauru")
                            if "Bauru" in LISTA_MUNIC else 0)
    with c2:
        limiar = st.slider("Limiar de alerta (escore z)", 2.0, 5.0, 3.0, 0.5)
    with c3:
        piso = st.slider("Piso de casos por dia", 0, 20, 3, 1)

    d = serie[serie["nome_munic"] == alvo].sort_values("datahora")
    info = municipios[municipios["nome_munic"] == alvo].iloc[0]
    alerta = (d["z"] >= limiar) & (d["casos_mm7d"] >= piso)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Grupo", f"{int(info['grupo'])}")
    k2.metric("População", f"{int(info['populacao']):,}".replace(",", "."))
    k3.metric("Incidência/100 mil", f"{info['Incidência/100 mil']:,.0f}".replace(",", "."))
    k4.metric("Dias com alerta", f"{int(alerta.sum())}")

    fig = go.Figure()
    for data in d.loc[alerta.fillna(False), "datahora"]:
        fig.add_vline(x=data, line=dict(color=TERRACOTA, width=1), opacity=0.20)
    fig.add_trace(go.Scatter(
        x=d["datahora"], y=d["casos_mm7d"], mode="lines",
        line=dict(color=VERDE, width=2), name="casos (média móvel de 7 dias)",
    ))
    st.plotly_chart(eixo_limpo(fig, "Novos casos por dia"), width="stretch")
    st.caption(
        "As faixas em laranja marcam os dias em que a média móvel excedeu o limiar "
        "escolhido em relação às quatro semanas anteriores. Ajuste o limiar e o piso "
        "acima para ver o efeito sobre o volume de alertas."
    )

    with st.expander("Perfil do município em relação à média estadual"):
        perfil = pd.DataFrame({
            "Atributo": ATRIBUTOS,
            "Escore z": [float(info[f"z_{a}"]) for a in ATRIBUTOS],
        })
        fig2 = px.bar(perfil, x="Escore z", y="Atributo", orientation="h",
                      color_discrete_sequence=[VERDE])
        fig2.update_layout(height=320)
        st.plotly_chart(eixo_limpo(fig2), width="stretch")


# ══════════════════════════════ AGRUPAMENTO ══════════════════════════════
elif pagina == "Agrupamento":
    st.title("Agrupamento dos municípios")
    st.write(
        "Os municípios foram agrupados por k-médias sobre sete atributos normalizados "
        "pela população. Contagens absolutas não são usadas: elas apenas separariam "
        "cidades grandes de pequenas."
    )

    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("Escolha de k")
        fig = px.line(silhueta, x="k", y="silhueta", markers=True,
                      color_discrete_sequence=[VERDE])
        fig.update_traces(line=dict(width=2), marker=dict(size=9))
        st.plotly_chart(eixo_limpo(fig, "Coeficiente de silhueta"), width="stretch")
        st.caption(
            f"Os valores variam entre {silhueta['silhueta'].min():.3f} e "
            f"{silhueta['silhueta'].max():.3f}. A faixa estreita indica que os municípios "
            "variam de modo contínuo, sem fronteiras nítidas — o critério estatístico, "
            "isoladamente, não determina a partição."
        )
    with c2:
        st.subheader("Perfil dos grupos")
        perfil = municipios.groupby("grupo")[[f"z_{a}" for a in ATRIBUTOS]].mean()
        perfil.columns = ATRIBUTOS
        fig = px.imshow(
            perfil, text_auto=".1f", aspect="auto", origin="upper",
            color_continuous_scale=[[0, AZUL], [0.5, "#f1f4f2"], [1, TERRACOTA]],
            zmin=-float(abs(perfil.values).max()), zmax=float(abs(perfil.values).max()),
            labels=dict(color="escore z"),
        )
        fig.update_layout(template="simple_white", height=380, font=dict(color=TINTA, size=12, family=FONTE),
                          margin=dict(l=10, r=10, t=30, b=10), xaxis_title="", yaxis_title="Grupo")
        st.plotly_chart(fig, width="stretch")

    st.subheader("Municípios por grupo")
    grupo_sel = st.multiselect("Filtrar grupos", sorted(municipios["grupo"].unique()),
                               default=sorted(municipios["grupo"].unique()))
    filtrado = municipios[municipios["grupo"].isin(grupo_sel)]

    # Um painel por grupo, com os demais municípios ao fundo em cinza. Quatro
    # cores sobrepostas não se distinguiriam com segurança no daltonismo mais
    # comum; painéis separados dispensam a comparação de matizes.
    fig = px.scatter(
        filtrado, x="Incidência/100 mil", y="Letalidade aparente",
        facet_col="grupo", facet_col_wrap=2, size="populacao", size_max=22,
        hover_name="nome_munic", opacity=0.8,
        color_discrete_sequence=[VERDE],
    )
    fig.update_traces(marker=dict(line=dict(width=0.6, color="white")))
    for eixo in fig.layout.annotations:
        eixo.text = eixo.text.replace("grupo=", "Grupo ")
        eixo.font = dict(size=13, family=FONTE, color=TINTA)
    fig = eixo_limpo(fig, "Letalidade aparente (%)")
    fig.update_layout(height=620, showlegend=False)
    st.plotly_chart(fig, width="stretch")
    st.caption(
        "Os eixos são compartilhados entre os painéis, o que permite comparar a "
        "posição de cada grupo. O tamanho do círculo indica a população."
    )

    for g in sorted(filtrado["grupo"].unique()):
        st.caption(f"**Grupo {g}** — {DESCRICAO_GRUPOS[g]}")

    st.dataframe(
        filtrado[["nome_munic", "grupo", "populacao"] + ATRIBUTOS]
        .rename(columns={"nome_munic": "Município", "grupo": "Grupo", "populacao": "População"})
        .sort_values(["Grupo", "Município"]),
        width="stretch", hide_index=True,
    )


# ══════════════════════════════ ALERTA PRECOCE ══════════════════════════════
elif pagina == "Alerta precoce":
    st.title("Alerta precoce de surtos")
    st.write(
        "O detector não prevê quantos casos haverá. Ele compara a média móvel de cada "
        "município com o comportamento das quatro semanas anteriores e sinaliza quando "
        "a série rompe o próprio padrão."
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        data_sel = st.date_input("Data de referência", value=DATA_MAX.date(),
                                 min_value=DATA_MIN.date(), max_value=DATA_MAX.date())
    with c2:
        limiar = st.select_slider("Limiar (escore z)", options=[2.0, 2.5, 3.0, 3.5, 4.0], value=3.0)
    with c3:
        piso = st.slider("Piso de casos por dia", 0, 20, 3, 1)

    dia = serie[serie["datahora"] == pd.Timestamp(data_sel)].copy()
    dia["em_alerta"] = (dia["z"] >= limiar) & (dia["casos_mm7d"] >= piso)
    em_alerta = dia[dia["em_alerta"]].merge(
        municipios[["nome_munic", "grupo"]], on="nome_munic", how="left"
    )

    linha = desempenho[desempenho["limiar"] == limiar].iloc[0]
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Municípios em alerta", f"{len(em_alerta)}")
    k2.metric("Cobertura dos picos", f"{linha['cobertura'] * 100:.1f}%")
    k3.metric("Antecedência mediana", f"{linha['antecedencia_mediana']:.0f} dias")
    k4.metric("Taxa de alerta", f"{linha['taxa_alerta'] * 100:.2f}%")

    st.subheader(f"Em alerta em {pd.Timestamp(data_sel):%d/%m/%Y}")
    if em_alerta.empty:
        st.info("Nenhum município ultrapassou o limiar nesta data.")
    else:
        tabela = (
            em_alerta[["nome_munic", "grupo", "casos_mm7d", "z", "pop"]]
            .sort_values("z", ascending=False)
            .rename(columns={"nome_munic": "Município", "grupo": "Grupo",
                             "casos_mm7d": "Casos/dia (mm7d)", "z": "Escore z",
                             "pop": "População"})
        )
        tabela["Casos/dia (mm7d)"] = tabela["Casos/dia (mm7d)"].round(1)
        tabela["Escore z"] = tabela["Escore z"].round(2)
        st.dataframe(tabela, width="stretch", hide_index=True)

    st.subheader("Calibração: o que se ganha e o que se paga")
    st.write(
        "Baixar o limiar detecta mais picos, mas sinaliza mais dias sem elevação "
        "sustentada. A escolha é do gestor, não do modelo."
    )
    tab = desempenho.copy()
    tab["cobertura"] = (tab["cobertura"] * 100).round(1)
    tab["taxa_alerta"] = (tab["taxa_alerta"] * 100).round(2)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=tab["taxa_alerta"], y=tab["cobertura"], mode="lines+markers+text",
                             text=[f"z={v}" for v in tab["limiar"]], textposition="bottom right",
                             line=dict(color=VERDE, width=2), marker=dict(size=10),
                             name="limiar"))
    fig.update_layout(xaxis_title="Taxa de alerta (% dos dias-município)")
    st.plotly_chart(eixo_limpo(fig, "Cobertura dos picos (%)"), width="stretch")

    st.dataframe(
        tab.rename(columns={
            "limiar": "Limiar (z)", "picos": "Picos avaliados", "cobertura": "Cobertura (%)",
            "antecedencia_mediana": "Antecedência mediana (dias)",
            "antecedencia_q1": "1º quartil", "antecedencia_q3": "3º quartil",
            "taxa_alerta": "Taxa de alerta (%)"}),
        width="stretch", hide_index=True,
    )
    st.caption(
        f"Avaliação retrospectiva sobre {int(picos[picos['limiar'] == limiar].shape[0]):,} picos "
        "identificados por proeminência. A antecedência é limitada a 60 dias pela janela de busca."
        .replace(",", ".")
    )


# ══════════════════════════════ COMPARATIVO ══════════════════════════════
elif pagina == "Comparativo":
    st.title("Comparativo entre municípios")

    escolhidos = st.multiselect(
        "Municípios", LISTA_MUNIC,
        default=[m for m in ["Bauru", "Campinas", "Ribeirão Preto"] if m in LISTA_MUNIC],
    )
    normalizar = st.checkbox("Normalizar por 100 mil habitantes", value=True)

    if not escolhidos:
        st.info("Selecione ao menos um município.")
    else:
        d = serie[serie["nome_munic"].isin(escolhidos)].copy()
        if normalizar:
            d["valor"] = d["casos_mm7d"] / d["pop"] * 1e5
            rotulo = "Novos casos por dia por 100 mil habitantes"
        else:
            d["valor"] = d["casos_mm7d"]
            rotulo = "Novos casos por dia"

        fig = px.line(d, x="datahora", y="valor", color="nome_munic",
                      color_discrete_sequence=CORES_GRUPO)
        fig.update_traces(line=dict(width=2))
        fig.update_layout(legend_title_text="")
        st.plotly_chart(eixo_limpo(fig, rotulo), width="stretch")

        resumo = municipios[municipios["nome_munic"].isin(escolhidos)][
            ["nome_munic", "grupo", "populacao"] + ATRIBUTOS
        ].rename(columns={"nome_munic": "Município", "grupo": "Grupo", "populacao": "População"})
        st.dataframe(resumo, width="stretch", hide_index=True)
        st.caption(
            "Sem normalização, a comparação entre municípios de portes distintos mede "
            "sobretudo o tamanho da população."
        )
