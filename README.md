# Painel COVID-19 - Estado de São Paulo

Análise temporal e espacial da pandemia de COVID-19 no Estado de São Paulo (2020–2023), com componentes de aprendizado de máquina para identificar padrões municipais e antecipar picos.

**Projeto Integrador em Computação IV (PJI410)** - Universidade Virtual do Estado de São Paulo (Univesp)

## O Aplicativo:

Aplicação web interativa com dois modelos de ML operacionais:

### 1. **Agrupamento Municipal** (K-Médias)
Identifica perfis de disseminação entre 645 municípios usando sete indicadores normalizados:
- Incidência e mortalidade (por 100 mil hab.)
- Letalidade aparente
- Altura do pico
- Variabilidade semanal
- Concentração pré-2022
- Escala populacional

Resultado: **4 grupos interpretáveis** de cidades com dinâmicas epidemiológicas semelhantes.

### 2. **Alerta Precoce** (Detecção de Anomalias)
Detecta quando a série de casos de um município rompe o padrão recente via escore z ajustável:
- **Cobertura**: 79% dos picos detectados com z ≥ 3,0
- **Antecedência mediana**: 31 dias antes do pico
- **Taxa de alerta**: 5,4% dos dias sinalizados (balanceado entre sensibilidade e especificidade)

## Como executar

### 1. Instale as dependências
```bash
pip install -r requirements.txt
```

### 2. Prepare os dados
```bash
python 01_preparar_dados.py     
python 02_agrupar.py             # clustering e silhueta
python 03_avaliar_alerta.py      # validação retrospectiva
```

O pipeline completo leva menos de 1 minuto.

### 3. Rode a aplicação
```bash
streamlit run app.py
```

Abra o navegador em `http://localhost:8501`

## Estrutura do repositório

```
painel-covid-sp/
├── 01_preparar_dados.py         # Etapa 1: limpeza, conversão, z-score
├── 02_agrupar.py                # Etapa 2: features, k-médias, silhueta
├── 03_avaliar_alerta.py         # Etapa 3: identificação de picos, validação
├── app.py                        # Interface Streamlit (5 seções)
├── requirements.txt
├── .streamlit/config.toml        # Tema e configurações
├── dados/                        # Parquets derivados (versionados)
│   ├── serie_municipal.parquet   # ~5,5 MB - série temporal por município
│   ├── features_municipios.parquet
│   ├── picos.parquet
│   └── desempenho_alerta.csv
│
└── pi3_original/                 # Versão histórica (PI III)
    ├── app.py                    # Visualizações básicas do Brener
    ├── requirements.txt
    └── dados/
        ├── macro/
        └── sao_paulo/
```

## Interface (5 seções)

| Seção | Função |
|---|---|
| **Visão Geral** | Série temporal agregada, estatísticas principais |
| **Município** | Série individual com alerta ajustável em tempo real |
| **Agrupamento** | Perfil dos 4 clusters (scatter facetado, acessível para daltonismo) |
| **Alerta Precoce** | Curva cobertura × taxa de alerta por limiar de z-score |
| **Comparativo** | Análise lado-a-lado de dois municípios |

Paleta de cores: verde (#3fa78a), terracota (#d97757), azul (#4a7fb5) — validada para acessibilidade.

## Metodologia

### Preparação (script 01)
- Remove categoria "Ignorado" (sem correspondência municipal)
- Ordena por município e data
- Calcula z-score da média móvel de 7 dias contra janela de referência (28 dias, defasagem de 7)
- Saída: 879.135 registros de 645 municípios

### Agrupamento (script 02)
- Normaliza 7 atributos por escore z
- K-médias para k ∈ [2, 8]
- Avalia silhueta (máximo em k=4, coef. 0,252)
- Gera escore z dos atributos para cada município (usado na interface)

### Validação (script 03)
- Identifica picos reais por proeminência (4.307 picos no total)
- Para cada limiar de z-score (2,0 a 4,0):
  - Mede **cobertura**: % de picos com ≥1 alerta nos 60 dias anteriores
  - Mede **antecedência**: dias entre primeiro alerta do episódio e pico
  - Mede **taxa de alerta**: % de dias-município sinalizados
- Resultado reportado na interface como função do limiar

## Dados

**Origem**: Secretaria de Estado da Saúde de São Paulo (Fundação Seade)  
**Repositório**: https://github.com/seade-R/dados-covid-sp  
**Período**: 25/02/2020 a 18/11/2023  
**Cobertura**: 645 municípios


## Requisitos

- Python 3.10+
- Streamlit, Pandas, PyArrow, Plotly
- scikit-learn (k-médias), SciPy (detecção de picos)

Veja `requirements.txt` para versões exatas.

##  Resultados principais

| Métrica | Valor |
|---|---|
| Municípios | 645 |
| Período | 1.389 dias |
| Registros totais | 879.135 |
| Coeficiente de silhueta (k=4) | 0,252 |
| Cobertura de picos (z ≥ 3,0) | 79,0% |
| Taxa de alerta (z ≥ 3,0) | 5,41% |
| Antecedência mediana (z ≥ 3,0) | 31 dias |

## Histórico

**PI III** (covidestadodesp): Visualizações exploratórias (macro, estadual, municipal).  
**PI IV** (atual): Arquitetura completa com ML — clustering e alerta precoce validados retrospectivamente.

Ambas as versões estão no repositório para referência.

##  Implantação em nuvem

O painel pode ser publicado no [Streamlit Community Cloud](https://streamlit.io/cloud):

1. Aponte para este repositório
2. Indique `app.py` como arquivo principal
3. Parquets derivados já estão versionados
4. CSV bruto é baixado na primeira execução

## Notas metodológicas

- **Escore z**: Calcula-se contra janela móvel recente (não contra série inteira) para que o próprio crescimento inicial da epidemia não contamine a detecção.
- **Silhueta baixa (0,252)**: Reflete variação contínua em atributos naturais (cidades grandes vs. pequenas têm dinâmicas diferentes), não falta de clustering.
- **Validação retrospectiva**: A série termina em nov/2023. Alertas são validados contra picos já ocorridos — mede-se capacidade de antecipação, não previsão futura.
- **Acessibilidade**: Paleta de cores passou por validação para daltonismo; gráficos de cluster usam facetas (4 painéis) em vez de cores sobrepostas.

##  Autores

- Beatriz Sailer
- Brener (PI III)
-

Assistência técnica

Claude (IA) - desenvolvimento da interface Streamlit, estilização visual, acessibilidade (validação de cores para daltonismo), configuração de tema e CSS.

##  Licença
MIT

MIT

---

Para dúvidas, consulte o [relatório técnico](./Relatório_Parcial_PI_IV.docx) (28 páginas, figuras e quadros).
