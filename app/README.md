# Painel COVID-19 - Estado de São Paulo

Projeto Integrador em Computação IV (PJI410) — Universidade Virtual do Estado de São Paulo.

Aplicação web interativa sobre a série municipal de casos e óbitos de COVID-19 divulgada
pela Fundação Seade, com duas camadas de aprendizado de máquina:

- **Agrupamento** dos 645 municípios por perfil de disseminação (k-médias sobre sete
  atributos normalizados pela população);
- **Alerta precoce** por detecção de anomalias — o sistema não prevê quantos casos
  haverá, sinaliza quando a série de um município rompe o próprio padrão recente.

## Como executar

Requer Python 3.10 ou superior.

```bash
pip install -r requirements.txt

python 01_preparar_dados.py     # baixa a base e grava dados/serie_municipal.parquet
python 02_agrupar.py            # atributos, k-médias e coeficiente de silhueta
python 03_avaliar_alerta.py     # avaliação retrospectiva do detector

streamlit run app.py
```

O primeiro script baixa cerca de 77 MB na primeira execução e grava uma versão
comprimida de aproximadamente 5,5 MB. As execuções seguintes reaproveitam o arquivo
já baixado. O pipeline completo leva menos de um minuto.

## Estrutura

| Arquivo | Papel |
|---|---|
| `01_preparar_dados.py` | Limpeza, conversão para Parquet e cálculo do escore z por município |
| `02_agrupar.py` | Sete atributos por município, k-médias para k de 2 a 8, silhueta |
| `03_avaliar_alerta.py` | Identificação de picos e avaliação do detector por limiar |
| `app.py` | Interface Streamlit com cinco seções |
| `dados/` | Base bruta (não versionada) e artefatos derivados (versionados) |

O escore z é calculado uma única vez, no pipeline. O limiar de alerta fica ajustável
na interface, o que permite explorar a calibração sem recalcular nada.

## Decisões de tratamento

**A categoria "Ignorado" é removida.** Ela não corresponde a município algum e não tem
população de referência, o que a torna inadequada a qualquer indicador normalizado.

**As 1.247 variações diárias negativas ficam todas dentro dessa categoria.** Elas
decorrem de retificações retroativas: quando a fonte reclassifica um caso antes sem
município, a categoria residual é descontada e fica negativa. Depois da remoção, nenhuma
série municipal apresenta variação negativa.

**Nenhum atributo do agrupamento é contagem absoluta.** Todos são normalizados pela
população ou adimensionais. Sem isso, o agrupamento apenas separaria cidades grandes de
pequenas.

**A avaliação do detector é retrospectiva.** A série termina em 18/11/2023, data em que o
repositório deixou de ser atualizado. Os alertas são confrontados com picos já ocorridos:
o que se mede é a capacidade do método de antecipá-los.

## Como ler os resultados do alerta

Duas medidas, sempre juntas:

- **cobertura** — proporção de picos precedidos por ao menos um alerta;
- **taxa de alerta** — proporção de dias-município sinalizados, isto é, o custo em avisos
  a verificar.

Cobertura alta com taxa de alerta alta não é mérito: avisar todos os dias "detecta" tudo.
A seção *Alerta precoce* do painel mostra as duas em conjunto para cada limiar.

## Publicação

O painel pode ser publicado no Streamlit Community Cloud apontando para este repositório
e indicando `app.py` como arquivo principal. Para que funcione:

- os arquivos de `dados/` com extensão `.parquet` e `.csv` derivados **devem** estar
  versionados (somam poucos megabytes);
- o arquivo bruto `dados/dados_covid_sp.csv` **não** deve ser versionado — está no
  `.gitignore` e é baixado na primeira execução.

## Fonte dos dados

Secretaria de Estado da Saúde de São Paulo, organização da Fundação Seade.
Repositório: https://github.com/seade-R/dados-covid-sp
Série de 25/02/2020 a 18/11/2023.
