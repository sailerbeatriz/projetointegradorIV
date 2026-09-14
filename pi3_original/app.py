"""
COVID-19 — Visualização Interativa de Dados
Projeto Integrador em Computação I — Univesp
Framework: Streamlit + Pandas + Plotly

Para rodar:  py -m streamlit run app.py
Instalar:   py -m pip install streamlit pandas plotly
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ──────────────────────────────────────────────
# CONFIGURAÇÃO DA PÁGINA
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="COVID-19 — Painel Interativo",
    page_icon="🦠",
    layout="wide",
)

# ──────────────────────────────────────────────
# FUNÇÕES DE CARREGAMENTO DE DADOS
# ──────────────────────────────────────────────

@st.cache_data
def carregar_br():
    df = pd.read_csv(r"dados\macro\br.csv", sep=";", parse_dates=["datahora"])
    df = df.sort_values("datahora").reset_index(drop=True)
    df["novos_casos"] = df["casos_acum"].diff().fillna(0).clip(lower=0).astype(int)
    df["novos_obitos"] = df["obitos_acum"].diff().fillna(0).clip(lower=0).astype(int)
    df["mes"] = df["datahora"].dt.to_period("M").astype(str)
    return df


@st.cache_data
def carregar_sp():
    df = pd.read_csv(r"dados\sao_paulo\sp.csv", sep=";", parse_dates=["datahora"])
    df = df.sort_values("datahora").reset_index(drop=True)
    df["novos_casos"] = df["casos_acum"].diff().fillna(0).clip(lower=0).astype(int)
    df["novos_obitos"] = df["obitos_acum"].diff().fillna(0).clip(lower=0).astype(int)
    df["mes"] = df["datahora"].dt.to_period("M").astype(str)
    return df


@st.cache_data
def carregar_mundo():
    df = pd.read_csv(r"dados\macro\mundo.csv", sep=";", parse_dates=["datahora"])
    df = df.sort_values("datahora").reset_index(drop=True)
    df["novos_casos"] = df["casos_acum"].diff().fillna(0).clip(lower=0).astype(int)
    df["novos_obitos"] = df["obitos_acum"].diff().fillna(0).clip(lower=0).astype(int)
    df["mes"] = df["datahora"].dt.to_period("M").astype(str)
    return df


@st.cache_data
def carregar_municipios():
    df = pd.read_csv(
        r"dados\sao_paulo\municipios.csv", sep=";", encoding="cp1252"
    )
    df.columns = ["cod_ibge", "regiao", "municipio", "casos_acum", "obitos_acum"]
    df["letalidade_pct"] = ((df["obitos_acum"] / df["casos_acum"]) * 100).round(2)
    return df


@st.cache_data
def carregar_dados_covid_sp():
    """Arquivo principal com série temporal por município."""
    df = pd.read_csv(
        r"dados\sao_paulo\dados_covid_sp.csv",
        sep=";",
        encoding="utf-8",
        parse_dates=["datahora"],
        dtype={"codigo_ibge": str},
    )
    # Corrigir colunas numéricas que podem ter vírgula como decimal
    for col in ["casos_novos", "obitos_novos", "latitude", "longitude", "casos", "obitos"]:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(",", ".", regex=False)
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Criar coluna de ano-mês para agrupamentos
    df["ano_mes"] = df["datahora"].dt.to_period("M").astype(str)
    df["ano"] = df["datahora"].dt.year

    return df


# ──────────────────────────────────────────────
# CARREGAMENTO
# ──────────────────────────────────────────────
try:
    df_br = carregar_br()
    df_sp = carregar_sp()
    df_mundo = carregar_mundo()
    df_mun = carregar_municipios()
    df_covid_sp = carregar_dados_covid_sp()
except Exception as e:
    st.error(
        f"Erro ao carregar os dados: {e}\n\n"
        "Verifique se as pastas 'dados/macro' e 'dados/sao_paulo' "
        "estão no mesmo diretório do app.py."
    )
    st.stop()

# ──────────────────────────────────────────────
# BARRA LATERAL — NAVEGAÇÃO
# ──────────────────────────────────────────────
st.sidebar.title("🦠 COVID-19 SP")
st.sidebar.caption("Projeto Integrador — Univesp")

pagina = st.sidebar.radio(
    "Navegação",
    [
        "📈 Evolução Temporal",
        "🗺️ Mapa de Calor SP",
        "📉 Curva por Cidade",
        "🏙️ Municípios SP",
        "📊 Comparativo",
    ],
)

# ══════════════════════════════════════════════
# PÁGINA 1 — EVOLUÇÃO TEMPORAL
# ══════════════════════════════════════════════
if pagina == "📈 Evolução Temporal":

    st.title("Evolução de Novos Casos e Óbitos")
    st.markdown(
        "Visualize a **flutuação semanal** ou **mensal** de novos casos e óbitos, "
        "permitindo identificar as ondas de COVID-19."
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        agrupamento = st.selectbox(
            "Agrupar por", ["Semana epidemiológica", "Mês"]
        )
    with col2:
        metrica = st.selectbox("Métrica", ["Novos casos", "Novos óbitos"])
    with col3:
        regioes = st.multiselect(
            "Regiões para exibir",
            ["Brasil", "São Paulo", "Mundo"],
            default=["Brasil", "São Paulo"],
        )

    coluna = "novos_casos" if metrica == "Novos casos" else "novos_obitos"
    grupo = "semana_epidem" if agrupamento == "Semana epidemiológica" else "mes"

    frames = []
    if "Brasil" in regioes:
        temp = df_br.groupby(grupo)[coluna].sum().reset_index()
        temp["local"] = "Brasil"
        frames.append(temp)
    if "São Paulo" in regioes:
        temp = df_sp.groupby(grupo)[coluna].sum().reset_index()
        temp["local"] = "São Paulo"
        frames.append(temp)
    if "Mundo" in regioes:
        temp = df_mundo.groupby(grupo)[coluna].sum().reset_index()
        temp["local"] = "Mundo"
        frames.append(temp)

    if frames:
        df_plot = pd.concat(frames, ignore_index=True)
        df_plot = df_plot.rename(columns={grupo: "periodo", coluna: "valor"})

        fig = px.line(
            df_plot,
            x="periodo",
            y="valor",
            color="local",
            labels={
                "periodo": agrupamento,
                "valor": metrica,
                "local": "Região",
            },
            title=f"{metrica} por {agrupamento.lower()}",
        )
        fig.update_layout(
            hovermode="x unified", template="plotly_white", height=500
        )
        st.plotly_chart(fig, use_container_width=True)

        # Cartões resumo
        st.subheader("Resumo geral (acumulado mais recente)")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Brasil — Casos", f"{df_br['casos_acum'].iloc[-1]:,.0f}")
            st.metric("Brasil — Óbitos", f"{df_br['obitos_acum'].iloc[-1]:,.0f}")
        with c2:
            st.metric("São Paulo — Casos", f"{df_sp['casos_acum'].iloc[-1]:,.0f}")
            st.metric("São Paulo — Óbitos", f"{df_sp['obitos_acum'].iloc[-1]:,.0f}")
        with c3:
            st.metric("Mundo — Casos", f"{df_mundo['casos_acum'].iloc[-1]:,.0f}")
            st.metric("Mundo — Óbitos", f"{df_mundo['obitos_acum'].iloc[-1]:,.0f}")
    else:
        st.warning("Selecione pelo menos uma região.")


# ══════════════════════════════════════════════
# PÁGINA 2 — MAPA DE CALOR SP
# ══════════════════════════════════════════════
elif pagina == "🗺️ Mapa de Calor SP":

    st.title("Mapa de Novos Casos por Município")
    st.markdown(
        "Observe como as **ondas de contágio se espalham** pelo Estado de São Paulo. "
        "Selecione um mês para ver a intensidade de novos casos em cada município. "
        "Tente comparar meses de férias (janeiro, julho) com meses seguintes para "
        "perceber o padrão litoral → interior."
    )

    # --- Controles ---
    col1, col2 = st.columns(2)

    with col1:
        anos_disp = sorted(df_covid_sp["ano"].dropna().unique())
        ano_sel = st.selectbox("Ano", anos_disp, index=len(anos_disp) - 2)

    meses_no_ano = (
        df_covid_sp[df_covid_sp["ano"] == ano_sel]["datahora"]
        .dt.month.dropna().unique()
    )
    meses_nomes = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
    }
    meses_disp = sorted(meses_no_ano)

    with col2:
        mes_sel = st.selectbox(
            "Mês",
            meses_disp,
            format_func=lambda m: meses_nomes.get(m, str(m)),
        )

    metrica_mapa = st.radio(
        "Métrica do mapa",
        ["Novos casos", "Novos óbitos"],
        horizontal=True,
    )
    col_metrica = "casos_novos" if metrica_mapa == "Novos casos" else "obitos_novos"

    # --- Filtrar e agrupar por município no mês selecionado ---
    mask = (df_covid_sp["ano"] == ano_sel) & (df_covid_sp["datahora"].dt.month == mes_sel)
    df_mes = df_covid_sp[mask].copy()

    df_mapa = (
        df_mes.groupby(["nome_munic", "latitude", "longitude"])
        .agg(total=pd.NamedAgg(column=col_metrica, aggfunc="sum"))
        .reset_index()
    )
    df_mapa = df_mapa.dropna(subset=["latitude", "longitude"])
    df_mapa = df_mapa[df_mapa["total"] > 0]

    if df_mapa.empty:
        st.warning("Sem dados para esse período.")
    else:
        fig = px.scatter_mapbox(
            df_mapa,
            lat="latitude",
            lon="longitude",
            size="total",
            color="total",
            color_continuous_scale="YlOrRd",
            size_max=40,
            hover_name="nome_munic",
            hover_data={"total": True, "latitude": False, "longitude": False},
            labels={"total": metrica_mapa},
            title=f"{metrica_mapa} — {meses_nomes[mes_sel]} de {ano_sel}",
            zoom=5.5,
            center={"lat": -22.5, "lon": -48.5},
            mapbox_style="carto-positron",
            height=650,
        )
        fig.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0})
        st.plotly_chart(fig, use_container_width=True)

        # Top 10 do mês
        st.subheader(f"Top 10 municípios — {meses_nomes[mes_sel]}/{ano_sel}")
        top10 = df_mapa.nlargest(10, "total")[["nome_munic", "total"]].reset_index(drop=True)
        top10.columns = ["Município", metrica_mapa]
        st.dataframe(top10, use_container_width=True)


# ══════════════════════════════════════════════
# PÁGINA 3 — CURVA POR CIDADE
# ══════════════════════════════════════════════
elif pagina == "📉 Curva por Cidade":

    st.title("Curva de Novos Casos por Cidade")
    st.markdown(
        "Selecione uma ou mais cidades para visualizar a **evolução dos novos contágios** "
        "ao longo do tempo. Útil para identificar em qual período cada município "
        "enfrentou seus piores momentos."
    )

    # Lista de municípios disponíveis
    municipios_disp = sorted(df_covid_sp["nome_munic"].dropna().unique())

    # Polos do grupo como sugestão
    polos_sugestao = [
        m for m in ["Fernandópolis", "Votuporanga", "São Paulo"]
        if m in municipios_disp
    ]

    cidades_sel = st.multiselect(
        "Selecione os municípios (máx. 8)",
        municipios_disp,
        default=polos_sugestao,
        max_selections=8,
    )

    col1, col2 = st.columns(2)
    with col1:
        metrica_curva = st.selectbox(
            "Métrica",
            ["Novos casos", "Novos óbitos"],
            key="metrica_curva",
        )
    with col2:
        agrupar_curva = st.selectbox(
            "Agrupar por",
            ["Mês", "Semana (dado bruto)"],
            key="agrupar_curva",
        )

    col_metrica_curva = (
        "casos_novos" if metrica_curva == "Novos casos" else "obitos_novos"
    )

    if cidades_sel:
        df_cidades = df_covid_sp[
            df_covid_sp["nome_munic"].isin(cidades_sel)
        ].copy()

        if agrupar_curva == "Mês":
            df_curva = (
                df_cidades.groupby(["nome_munic", "ano_mes"])[col_metrica_curva]
                .sum()
                .reset_index()
            )
            df_curva = df_curva.rename(
                columns={"ano_mes": "periodo", col_metrica_curva: "valor"}
            )
        else:
            df_curva = (
                df_cidades.groupby(["nome_munic", "datahora"])[col_metrica_curva]
                .sum()
                .reset_index()
            )
            df_curva = df_curva.rename(
                columns={"datahora": "periodo", col_metrica_curva: "valor"}
            )

        fig = px.line(
            df_curva,
            x="periodo",
            y="valor",
            color="nome_munic",
            labels={
                "periodo": "Período",
                "valor": metrica_curva,
                "nome_munic": "Município",
            },
            title=f"{metrica_curva} ao longo do tempo",
        )
        fig.update_layout(
            hovermode="x unified", template="plotly_white", height=500
        )
        st.plotly_chart(fig, use_container_width=True)

        # Resumo em tabela
        st.subheader("Resumo por município selecionado")
        resumo = (
            df_cidades.groupby("nome_munic")
            .agg(
                total_casos=pd.NamedAgg(column="casos_novos", aggfunc="sum"),
                total_obitos=pd.NamedAgg(column="obitos_novos", aggfunc="sum"),
                pico_casos=pd.NamedAgg(column="casos_novos", aggfunc="max"),
            )
            .reset_index()
        )
        resumo.columns = [
            "Município", "Total de Casos", "Total de Óbitos", "Pico (casos em 1 registro)"
        ]
        st.dataframe(resumo, use_container_width=True)
    else:
        st.info("Selecione pelo menos uma cidade.")


# ══════════════════════════════════════════════
# PÁGINA 4 — MUNICÍPIOS SP (TABELA)
# ══════════════════════════════════════════════
elif pagina == "🏙️ Municípios SP":

    st.title("Municípios do Estado de São Paulo")
    st.markdown(
        "Veja a **taxa de letalidade** (óbitos / casos) por município e "
        "identifique quais regiões foram mais afetadas."
    )

    col1, col2 = st.columns(2)

    with col1:
        regioes_disp = sorted(df_mun["regiao"].dropna().unique())
        filtro_regiao = st.multiselect(
            "Filtrar por região", regioes_disp, default=regioes_disp
        )
    with col2:
        ordenar_por = st.selectbox(
            "Ordenar por",
            ["letalidade_pct", "casos_acum", "obitos_acum"],
            format_func=lambda x: {
                "letalidade_pct": "Taxa de letalidade (%)",
                "casos_acum": "Casos acumulados",
                "obitos_acum": "Óbitos acumulados",
            }[x],
        )

    df_filtrado = df_mun[df_mun["regiao"].isin(filtro_regiao)].sort_values(
        ordenar_por, ascending=False
    )

    polos = ["Fernandópolis", "Icém", "Paulo de Faria", "Riolândia", "Votuporanga"]
    destaque = st.checkbox("Destacar municípios dos polos do grupo", value=True)

    top = df_filtrado.head(20)
    fig = px.bar(
        top,
        x="municipio",
        y=ordenar_por,
        color="regiao",
        labels={
            "municipio": "Município",
            "letalidade_pct": "Letalidade (%)",
            "casos_acum": "Casos acumulados",
            "obitos_acum": "Óbitos acumulados",
            "regiao": "Região",
        },
        title=f"Top 20 municípios — {ordenar_por.replace('_', ' ').title()}",
    )
    fig.update_layout(template="plotly_white", xaxis_tickangle=-45, height=500)
    st.plotly_chart(fig, use_container_width=True)

    if destaque:
        st.subheader("Dados dos municípios-polo do grupo")
        df_polos = df_mun[df_mun["municipio"].isin(polos)]
        if not df_polos.empty:
            st.dataframe(
                df_polos[
                    ["municipio", "regiao", "casos_acum", "obitos_acum", "letalidade_pct"]
                ]
                .sort_values("letalidade_pct", ascending=False)
                .reset_index(drop=True),
                use_container_width=True,
            )
        else:
            st.info("Nenhum dos polos foi encontrado nos dados.")

    st.subheader("Buscar município")
    busca = st.text_input("Digite o nome do município")
    if busca:
        resultado = df_filtrado[
            df_filtrado["municipio"].str.contains(busca, case=False, na=False)
        ]
        st.dataframe(resultado.reset_index(drop=True), use_container_width=True)


# ══════════════════════════════════════════════
# PÁGINA 5 — COMPARATIVO
# ══════════════════════════════════════════════
elif pagina == "📊 Comparativo":

    st.title("Comparativo entre Municípios")
    st.markdown(
        "Selecione municípios para comparar seus números lado a lado."
    )

    todos_municipios = sorted(df_mun["municipio"].tolist())
    polos_default = [
        m for m in ["Fernandópolis", "Votuporanga"]
        if m in todos_municipios
    ]

    selecionados = st.multiselect(
        "Escolha os municípios (máx. 10)",
        todos_municipios,
        default=polos_default,
        max_selections=10,
    )

    if selecionados:
        df_comp = df_mun[df_mun["municipio"].isin(selecionados)].copy()

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                name="Casos acumulados",
                x=df_comp["municipio"],
                y=df_comp["casos_acum"],
                marker_color="#636EFA",
            )
        )
        fig.add_trace(
            go.Bar(
                name="Óbitos acumulados",
                x=df_comp["municipio"],
                y=df_comp["obitos_acum"],
                marker_color="#EF553B",
            )
        )
        fig.update_layout(
            barmode="group",
            template="plotly_white",
            title="Casos e Óbitos — Comparativo",
            height=450,
        )
        st.plotly_chart(fig, use_container_width=True)

        fig2 = px.bar(
            df_comp,
            x="municipio",
            y="letalidade_pct",
            color="municipio",
            title="Taxa de Letalidade (%) — Comparativo",
            labels={
                "municipio": "Município",
                "letalidade_pct": "Letalidade (%)",
            },
        )
        fig2.update_layout(
            template="plotly_white", showlegend=False, height=400
        )
        st.plotly_chart(fig2, use_container_width=True)

        st.dataframe(
            df_comp[
                ["municipio", "regiao", "casos_acum", "obitos_acum", "letalidade_pct"]
            ]
            .sort_values("casos_acum", ascending=False)
            .reset_index(drop=True),
            use_container_width=True,
        )
    else:
        st.info("Selecione pelo menos um município para comparar.")


# ──────────────────────────────────────────────
# RODAPÉ
# ──────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.markdown(
    "**Fonte dos dados:** [Governo do Estado de SP]"
    "(https://www.seade.gov.br/coronavirus/)"
)
st.sidebar.markdown("Projeto Integrador em Computação I — Univesp 2026")
