Com base no seu documento de planejamento e na estrutura de pastas sugerida, aqui está uma proposta de **README.md** completa e profissional para o seu projeto. [cite_start]Este ficheiro foi estruturado para servir de guia tanto para si quanto para os avaliadores (Renan e Rebecka) durante as três etapas da disciplina[cite: 6, 7, 112].

---

# Análise da relação entre casos de COVID-19, vacinação e taxa de mortalidade no Brasil

[cite_start]Este projeto faz parte da disciplina **ACH2177 - Introdução à Ciência de Dados** e visa investigar como a interação entre o número de casos confirmados, o nível de cobertura vacinal e a localização geográfica influenciou a taxa de mortalidade por COVID-19 nos estados brasileiros[cite: 1, 4, 18].

## 📋 Equipa
* [cite_start]Renan Gomes Miranda Costa - 14616462 [cite: 6]
* [cite_start]Rebecka Bocci Domingues - 15486608 [cite: 7]

## 🎯 Questões de Pesquisa
[cite_start]O estudo procura responder à questão geral: *"Como a interação entre o número de casos confirmados, o nível de cobertura vacinal e a unidade federativa influencia a taxa de mortalidade por COVID-19 nos estados brasileiros?"*[cite: 18].

[cite_start]As questões secundárias incluem[cite: 19]:
* [cite_start]Identificar se existe um limiar de cobertura vacinal para a queda significativa da mortalidade[cite: 20].
* [cite_start]Analisar padrões regionais distintos entre as cinco regiões do Brasil[cite: 21].
* [cite_start]Avaliar a capacidade de predição da taxa de mortalidade semanal através de modelos de Machine Learning[cite: 16].

## 📂 Estrutura do Projeto
```text
.
├── data/
│   ├── raw/                # Dados originais de Wesley Cota (covid19br)
│   ├── processed/          # Dados limpos e agregados por semana epidemiológica
│   └── sample/             # Subamostra estratificada de 30% para exploração
├── notebooks/
│   ├── 01_exploracao.ipynb # Análise exploratória e visualizações 
│   └── 02_modelagem.ipynb  # Implementação de Regressão, Random Forest e XGBoost 
├── figures/                # Gráficos, mapas e heatmaps gerados
├── reports/                # PDFs dos trabalhos entregues 
├── requirements.txt        # Dependências do projeto
└── README.md
```

## 📊 Dados Utilizados
[cite_start]A base de dados é mantida por **Wesley Cota**, compilando dados do OpenDataSUS e secretarias estaduais[cite: 27, 28].
* [cite_start]**Período:** Fevereiro de 2020 até o último registo disponível[cite: 25].
* [cite_start]**Frequência:** Diária (agregada semanalmente para a modelagem)[cite: 28, 95].
* [cite_start]**Amostragem:** Para a fase exploratória, será utilizada uma amostragem estratificada de 30% da base[cite: 37, 38].

## 🚀 Modelagem
[cite_start]Para a tarefa de regressão supervisionada, serão avaliados os seguintes modelos[cite: 81, 82]:
1.  [cite_start]**Regressão Linear Múltipla** (Baseline)[cite: 83].
2.  [cite_start]**Random Forest Regressor** (Captura de não-linearidades)[cite: 85].
3.  [cite_start]**Gradient Boosting (XGBoost/LightGBM)**[cite: 87].

## 📅 Cronograma de Entregas
* [cite_start]**Trabalho 1:** Planeamento (12/04/2026)[cite: 112, 113].
* [cite_start]**Trabalho 2:** Exploração de Dados (10/05/2026)[cite: 112, 113].
* [cite_start]**Trabalho 3:** Modelagem e Avaliação Final (28/06/2026)[cite: 112, 113].

## 🛠️ Como Executar
1. Instale as dependências: `pip install -r requirements.txt`
2. [cite_start]Os dados brutos devem ser colocados em `data/raw/` (consulte as referências para o link do repositório)[cite: 27].
3. [cite_start]Execute o notebook `01_exploracao.ipynb` para visualizar a curadoria e análise inicial[cite: 113].

## 📚 Referências
* Cota, W. (2020). [cite_start]Monitoring the number of COVID-19 cases and deaths in Brazil. [cite: 115]
* [cite_start]Repositório: [https://github.com/wcota/covid19br](https://github.com/wcota/covid19br) [cite: 118]