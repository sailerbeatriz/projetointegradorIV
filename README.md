# Painel COVID-19 – Estado de São Paulo

**Aplicação online: [painelcovidsp.streamlit.app](https://painelcovidsp.streamlit.app/)**

Análise temporal e espacial da pandemia de COVID-19 no Estado de São Paulo (2020–2023), com aprendizado de máquina para caracterizar perfis municipais e avaliar, de forma retrospectiva, um método de alerta para elevações atípicas de casos.

Projeto Integrador em Computação IV (PJI410) – Universidade Virtual do Estado de São Paulo (Univesp)

Relatório técnico: [`docs/Relatorio_Parcial_PI_IV.pdf`](docs/Relatorio_Parcial_PI_IV.pdf)

## O aplicativo

Aplicação web interativa (Streamlit) com dois modelos integrados.

### 1. Agrupamento municipal (k-médias)

Agrupa os 645 municípios a partir de sete indicadores padronizados por escore z:

- incidência acumulada por 100 mil habitantes
- mortalidade acumulada por 100 mil habitantes
- letalidade aparente
- altura do maior pico por 100 mil habitantes
- variabilidade semanal
- proporção dos casos até 31/12/2021
- logaritmo da população

A interface usa a partição em **4 grupos** como caracterização exploratória. O coeficiente de silhueta é baixo em todas as partições testadas, então os grupos resumem uma variação contínua entre municípios e não representam tipos bem separados (ver [Notas metodológicas](#notas-metodológicas)).

### 2. Alerta precoce (detecção de anomalias)

Sinaliza quando a média móvel de casos de um município ultrapassa o padrão recente, medido por escore z com limiar ajustável.

Resultados com limiar z ≥ 3,0, em avaliação retrospectiva:

- **Cobertura:** 94,6% dos picos tiveram ao menos um alerta nos 60 dias anteriores
- **Antecedência mediana:** 31 dias (intervalo interquartílico de 14 a 49 dias)
- **Taxa de alerta:** 5,41% dos dias-município sinalizados

Esses números ainda **não** foram comparados a uma linha de base aleatória e, por isso, não demonstram sozinhos capacidade de antecipação (ver [Limitações](#limitações-conhecidas)).

## Como executar

A aplicação está publicada em [painelcovidsp.streamlit.app](https://painelcovidsp.streamlit.app/) e não exige instalação. As instruções abaixo servem para rodar localmente ou para refazer a análise do zero.

### 1. Instale as dependências

```bash
pip install -r requirements.txt
```

Para reproduzir o ambiente exato usado na análise, use `requirements-lock.txt` no lugar de `requirements.txt`.

### 2. Rode a aplicação

```bash
streamlit run app.py
```

Abra o navegador em http://localhost:8501.

Os arquivos derivados estão versionados em `dados/`, então o aplicativo sobe sem precisar refazer o pipeline.

### 3. Refazer a análise (opcional)

```bash
python 01_preparar_dados.py      # limpeza, conversão e escore z
python 02_agrupar.py             # atributos, k-médias e silhueta
python 03_avaliar_alerta.py      # picos e avaliação retrospectiva
python 04_figuras.py             # figuras do relatório, 300 dpi
python 05_verificacoes.py        # confere os números do relatório
```

O primeiro script baixa o CSV da Fundação Seade (~77 MB) na primeira execução. O pipeline completo leva menos de 1 minuto, fora o download.

## Estrutura do repositório

```
projetointegradorIV/
├── 01_preparar_dados.py           # Etapa 1: limpeza, conversão, escore z
├── 02_agrupar.py                  # Etapa 2: atributos, k-médias, silhueta
├── 03_avaliar_alerta.py           # Etapa 3: identificação de picos, avaliação
├── 04_figuras.py                  # Etapa 4: figuras do relatório (Matplotlib)
├── 05_verificacoes.py             # Confere os números do relatório
├── app.py                         # Interface Streamlit (5 seções)
├── requirements.txt               # Dependências
├── requirements-lock.txt          # Versões exatas do ambiente da análise
├── .streamlit/config.toml         # Tema e configurações
├── .devcontainer/                 # Ambiente pronto para Codespaces
├── dados/                         # Arquivos derivados (versionados)
│   ├── serie_municipal.parquet    # ~5,5 MB – série diária por município
│   ├── features_municipios.parquet
│   ├── picos.parquet
│   ├── silhueta.csv
│   └── desempenho_alerta.csv
├── figuras/                       # PNGs do relatório, 300 dpi
│   ├── figura1_serie_estadual.png
│   ├── figura2_incidencia_letalidade.png
│   ├── figura3_silhueta.png
│   ├── figura4_perfil_grupos.png
│   └── figura5_bauru.png
├── docs/
│   └── Relatorio_Parcial_PI_IV.pdf
├── MAPA_DO_CODIGO.md              # Onde cada tecnologia é usada
├── LICENSE
└── pi3_original/                  # Versão histórica (PI III)
    ├── app.py                     # Visualizações do PI III
    ├── requirements.txt
    └── dados/
        ├── macro/
        └── sao_paulo/
```

O CSV bruto (`dados/dados_covid_sp.csv`) não é versionado: ele é baixado pelo script 01.

## Interface (5 seções)

| Seção | Função |
|---|---|
| Visão geral | Série temporal agregada do Estado, com seleção de período e métrica |
| Município | Série individual, com limiar e piso de alerta ajustáveis |
| Agrupamento | Curva de silhueta, mapa de calor do perfil dos 4 grupos e lista de municípios em facetas |
| Alerta precoce | Municípios em alerta em uma data escolhida e curva de cobertura × taxa de alerta por limiar |
| Comparativo | Dois ou mais municípios lado a lado, com opção de normalizar por 100 mil habitantes |

Paleta de cores: verde (#3fa78a), terracota (#d97757) e azul (#4a7fb5), validada para daltonismo. Os gráficos de grupo usam facetas e escala divergente em vez de cores categóricas sobrepostas.

## Metodologia

### Preparação (script 01)

- Remove a categoria “Ignorado”, que não tem município nem população de referência (1.363 registros, um por data)
- As 1.247 variações diárias negativas do arquivo original vêm de retificações da fonte e estão todas naquela categoria, então a base de trabalho fica sem valores negativos
- Ordena por município e data
- Calcula o escore z da média móvel de 7 dias em relação a uma janela de referência de 28 dias que termina 7 dias antes do dia avaliado
- Saída: 879.135 registros de 645 municípios

### Agrupamento (script 02)

- Padroniza os 7 atributos por escore z
- Executa o k-médias para k de 2 a 8 e calcula a silhueta de cada partição:

| k | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|
| Silhueta | **0,273** | 0,261 | 0,234 | 0,230 | 0,231 | 0,244 | 0,248 |

- Gera o escore z dos atributos de cada município, usado na interface

Caracterização da partição exploratória com k = 4:

| Grupo | Municípios | População mediana | Incidência /100 mil | Letalidade | Maior pico /100 mil | Casos até 2021 |
|---|---|---|---|---|---|---|
| 1 | 181 | 7.268 | 9.880 | 3,83% | 146 | 91% |
| 2 | 135 | 110.489 | 15.305 | 2,91% | 106 | 73% |
| 3 | 69 | 3.731 | 33.097 | 1,62% | 890 | 41% |
| 4 | 260 | 14.722 | 25.556 | 1,62% | 296 | 50% |

### Avaliação do alerta (script 03)

- Identifica picos por proeminência (`scipy.signal.find_peaks`): 4.307 picos no total
- Para cada limiar de escore z (2,0 a 4,0), calcula:
  - **cobertura:** % de picos com ao menos 1 alerta nos 60 dias anteriores
  - **antecedência:** dias entre o primeiro alerta nessa janela e o pico
  - **taxa de alerta:** % de dias-município sinalizados
- Alerta emitido quando z ≥ limiar e a média móvel é de pelo menos 3 casos diários

| Limiar z | Cobertura | Antecedência mediana | Q1–Q3 | Taxa de alerta |
|---|---|---|---|---|
| 2,0 | 98,1% | 35 dias | 18–54 | 7,74% |
| 2,5 | 96,7% | 33 dias | 16–51 | 6,42% |
| **3,0** | **94,6%** | **31 dias** | 14–49 | **5,41%** |
| 3,5 | 91,3% | 30 dias | 13–47 | 4,59% |
| 4,0 | 88,2% | 28 dias | 11–46 | 3,94% |

## Dados

- **Origem:** Secretaria de Estado da Saúde de São Paulo, organizados pela Fundação Seade
- **Repositório:** https://github.com/seade-R/dados-covid-sp
- **Período:** 25/02/2020 a 18/11/2023 (1.363 datas)
- **Registros:** 880.498 no arquivo original; 879.135 após remover “Ignorado”
- **Cobertura:** 645 municípios
- **Tamanho:** 76,9 MB em CSV → ~5,5 MB em Parquet

## Requisitos

- Python 3.10+
- Streamlit, Pandas, PyArrow, Plotly
- scikit-learn (k-médias), SciPy (detecção de picos)
- matplotlib (figuras do relatório)

Veja `requirements.txt` para as dependências e `requirements-lock.txt` para as versões exatas.

## Resultados principais

| Métrica | Valor |
|---|---|
| Municípios | 645 |
| Período | 25/02/2020 a 18/11/2023 (1.363 datas) |
| Registros (base tratada) | 879.135 |
| Silhueta máxima | 0,273 (k = 2) |
| Silhueta da partição usada (k = 4) | 0,234 |
| Picos identificados | 4.307 |
| Cobertura de picos (z ≥ 3,0) | 94,6% |
| Antecedência mediana (z ≥ 3,0) | 31 dias |
| Taxa de alerta (z ≥ 3,0) | 5,41% |

## Reprodutibilidade

- Partição do k-médias fixada por `random_state=42` e `n_init=10`, o que devolve os mesmos grupos em qualquer máquina
- Os arquivos derivados são versionados, então os números do relatório podem ser conferidos sem refazer o download
- `05_verificacoes.py` recalcula todos os valores citados no relatório e os imprime, sem alterar nenhum arquivo
- `MAPA_DO_CODIGO.md` liga cada tecnologia descrita no relatório ao arquivo e ao trecho correspondente

## Notas metodológicas

- **Escore z com janela móvel:** a referência é o comportamento recente do município, e não a série inteira. A defasagem de 7 dias impede que o início de uma subida entre no cálculo da própria referência, mesmo princípio da variante C2 do EARS (Hutwagner et al., 2003).
- **Silhueta baixa:** todas as partições ficam entre 0,230 e 0,273. Pelas faixas de Kaufman e Rousseeuw (1990), isso indica estrutura fraca (k = 2 e 3) ou ausência de estrutura substancial (k ≥ 4). Os municípios variam de forma contínua. Os 4 grupos servem para resumir essa variação e não devem ser lidos como tipos naturais.
- **Avaliação retrospectiva:** a série termina em novembro de 2023, e os alertas são comparados com picos já ocorridos. Mede-se se o método teria sinalizado antes do pico, não uma previsão de casos futuros.
- **Taxa de alerta ≠ taxa de falsos alarmes:** um dia com alerta pode corresponder a uma elevação real. A precisão dos alertas ainda não foi medida.
- **Acessibilidade:** a paleta foi validada para daltonismo, e os gráficos de grupo usam facetas (4 painéis) em vez de cores sobrepostas.

## Limitações conhecidas

- **Sem linha de base:** com taxa de alerta de ~5% e janela de 60 dias, alertas aleatórios também cairiam antes de muitos picos. A próxima etapa compara os resultados com os alertas deslocados aleatoriamente no tempo (deslocamento circular) e mede a precisão por episódio.
- **Antecedência truncada em 60 dias:** o primeiro alerta da janela pode pertencer a um episódio anterior ao pico.
- **Artefatos de notificação:** há períodos de zeros seguidos de salto (interrupção e acúmulo de notificações) que geram alertas sem relação com surtos. O tratamento está em desenvolvimento.
- **Grupos com populações pequenas:** as taxas por 100 mil oscilam muito em municípios de poucos milhares de habitantes (Grupo 3).
- **Dados consolidados:** a avaliação usa os dados já retificados, e não os disponíveis em cada data.

## Histórico

- **PI III** ([elbrener/covidestadodesp](https://github.com/elbrener/covidestadodesp)): visualizações exploratórias (macro, estadual e municipal).
- **PI IV** (este repositório): aplicação com agrupamento e alerta precoce avaliados retrospectivamente.

A versão do PI III está em `pi3_original/` para referência.

## Autores

Projeto Integrador em Computação IV – Univesp, 2026

- Beatriz Torres Sailer
- Brener Leopoldino
- Bruna Carolina Miranda da Silva
- Rafael Matheus Padilha
- Thayara Akemi Murakami Catan

Orientadora: Fernanda Viviani Reggiani

### Assistência técnica

Claude (IA): desenvolvimento da interface Streamlit, estilização visual, acessibilidade (validação de cores para daltonismo), configuração de tema e CSS.

As decisões de método, os parâmetros dos modelos e a interpretação dos resultados são dos autores.

## Referências

- HUTWAGNER, L. et al. The bioterrorism preparedness and response Early Aberration Reporting System (EARS). *Journal of Urban Health*, v. 80, supl. 1, p. i89-i96, 2003.
- KAUFMAN, L.; ROUSSEEUW, P. J. *Finding groups in data*: an introduction to cluster analysis. New York: John Wiley & Sons, 1990.

## Licença

MIT
