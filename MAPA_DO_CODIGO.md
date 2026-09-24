# Mapa do código — onde cada tecnologia é usada

Este documento conecta cada frase da seção de tecnologias do relatório ao **arquivo e trecho de código** correspondente. Use-o para, na defesa, apontar exatamente onde cada coisa acontece.

---

## Visão geral do pipeline

```
dados_covid_sp.csv (Fundação Seade, ~77 MB)
        │
        ▼
01_preparar_dados.py   →  serie_municipal.parquet      [Pandas]
        │
        ├──────────────────────────────┐
        ▼                              ▼
02_agrupar.py                    03_avaliar_alerta.py
  features_municipios.parquet      picos.parquet
  silhueta.csv                     desempenho_alerta.csv
  [scikit-learn + NumPy]           [NumPy + SciPy]
        │                              │
        ├──────────────┬───────────────┤
        ▼              ▼               ▼
04_figuras.py     05_verificacoes.py   app.py
  figuras/*.png     confere os         interface web
  [Matplotlib]      números            [Streamlit + Plotly]
```

Cada script roda de forma independente e grava sua saída, que os próximos consomem. Qualquer pessoa clona o repositório e reproduz tudo com quatro comandos.

---

## "Python como linguagem base"
Toda a aplicação é escrita em Python 3.10 ou superior. Ver qualquer um dos arquivos `.py`.

## "Pandas para manipulação da série em escala"
**Arquivo: `01_preparar_dados.py`**
- Leitura do CSV brasileiro (`sep=";"`, `decimal=","`) com `pd.read_csv`.
- Remoção da categoria residual "Ignorado", que não tem população de referência. As variações diárias negativas do arquivo original decorrem de retificações da fonte e se concentram nessa categoria, de modo que a base de trabalho fica sem valores negativos.
- Cálculo do escore z móvel com `groupby` + `shift(7)` + `rolling(28)`: a janela de referência vai dos dias t−34 a t−7, e o desvio-padrão tem piso de 0,5.
- Gravação em Parquet (`to_parquet`, compressão `zstd`): de 76,9 MB para cerca de 5,5 MB.

## "NumPy e SciPy para os cálculos estatísticos"
**Arquivo: `03_avaliar_alerta.py`**
- `import numpy as np` — operações vetoriais sobre as séries.
- `from scipy.signal import find_peaks` — identificação dos picos de cada município.
- Parâmetros `prominence=max(maximo * 0.20, 3)` e `height=max(maximo * 0.25, 5)` — limiares relativos ao máximo de cada município, o que evita concentrar os picos nas cidades grandes.
- Cruza cada pico com os dias de alerta e mede cobertura, antecedência e taxa de alerta.

O escore z em si é calculado em `01_preparar_dados.py` (coluna `z`).

## "Scikit-learn para o k-médias e a silhueta"
**Arquivo: `02_agrupar.py`**
- `StandardScaler` — padroniza os sete atributos por escore z.
- `KMeans(n_clusters=k, n_init=10, random_state=42)` — agrupa os municípios, k de 2 a 8. A semente fixa torna a partição reproduzível.
- `silhouette_score` — avalia cada partição.
- Função `construir_atributos` — monta os sete atributos normalizados pela população: incidência, mortalidade, letalidade aparente, altura do maior pico, coeficiente de variação da média móvel, proporção de casos até 2021 e logaritmo da população.

## "Matplotlib para as figuras do relatório"
**Arquivo: `04_figuras.py`**
- Gera as cinco figuras do relatório a partir dos parquets e do `silhueta.csv`, em PNG de 300 dpi, na pasta `figuras/`.
- Imprime uma linha de conferência por figura, com os valores que aparecem no texto.
- Formata os números no padrão brasileiro (vírgula decimal) e usa a paleta validada para daltonismo.

## "Plotly para gráficos interativos"
**Arquivo: `app.py`**
- `plotly.express` e `plotly.graph_objects` — séries temporais, alertas, perfil dos grupos e comparação entre municípios, todos com zoom e hover.

## "Streamlit para a interface web"
**Arquivo: `app.py`**
- `st.set_page_config`, `st.sidebar` e os filtros de município e período.
- `@st.cache_data` — mantém os dados em memória entre interações.
- Roda com `streamlit run app.py`.

## "Todas são bibliotecas consolidadas e de código aberto"
Ver `requirements.txt`. O arquivo declara versões mínimas; para travar o ambiente exato de uma execução, gere um `requirements-lock.txt` com `pip freeze`.

---

## Como as figuras do relatório foram feitas

O script **`04_figuras.py`** gera as cinco figuras a partir dos dados processados, com Matplotlib. Ele lê `serie_municipal.parquet`, `features_municipios.parquet` e `silhueta.csv`, e grava os PNGs em `figuras/`.

Para reproduzir: `python 04_figuras.py`. A saída no terminal traz os valores de cada figura, o que permite conferir antes de inserir no documento:

```
Figura 1: pico de 18.202 em 16/06/2021
Figura 2: n = 645, medianas 18.578 e 2,08%
Figura 3: máximo em k = 2 (0,273)
Figura 4: grupo 1 n=181, grupo 2 n=135, grupo 3 n=69, grupo 4 n=260
Figura 5 (Bauru): 8 picos, 179 dias com alerta
```

## Como conferir todos os números do relatório

O script **`05_verificacoes.py`** recalcula, do zero, o que está escrito no texto: contagens da base, tipo da média móvel, valores citados nas Figuras 1 e 2, silhueta por k, perfil dos grupos, a tabela de desempenho do detector e a contagem das falhas de notificação. Rode `python 05_verificacoes.py` e compare com o relatório.
