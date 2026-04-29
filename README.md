# 📊 Análise da Relação entre Casos de COVID-19, Vacinação e Mortalidade no Brasil

Este projeto faz parte da disciplina **ACH2177 - Introdução à Ciência de Dados** e tem como objetivo realizar um estudo exploratório e preditivo sobre o impacto da vacinação e a evolução da pandemia de COVID-19 nas 27 unidades federativas do Brasil.

---

## 👥 Autores

* Renan Gomes Miranda Costa
* Rebecka Bocci Domingues
---

## 📋 Objetivo do Projeto

Investigar como o número de casos confirmados, o avanço da cobertura vacinal e as características regionais se relacionam com a **taxa de mortalidade ao longo do tempo**.

---

## ❓ Questões de Pesquisa

### Geral

* Como a interação entre casos, vacinação e localização geográfica influencia a mortalidade por COVID-19?

### Secundárias

* Existe um limiar de cobertura vacinal para uma queda significativa da mortalidade?
* Há padrões regionais distintos entre as cinco regiões do Brasil?
* Como mudou a relação entre casos e óbitos nas diferentes ondas (Gamma, Omicron, etc.)?

---

## 📊 Base de Dados

* **Fonte:** Repositório `wcota/covid19br`, mantido por Wesley Cota
* **População:** Registros oficiais de casos, óbitos e vacinação das 27 UFs brasileiras desde fevereiro de 2020
* **Estrutura:** Painel temporal com **30.842 registros** e **26 colunas**

### ⚠️ Limitações

* Possível subnotificação (principalmente no início da pandemia)
* Atrasos de registro em finais de semana e feriados

---

## 🛠️ Metodologia e Modelagem

O projeto utiliza uma abordagem de **aprendizado de máquina supervisionado (regressão)** para prever a taxa de mortalidade semanal.

### 📌 Modelos Candidatos

* **Regressão Linear Múltipla**

  * Modelo baseline para avaliar a contribuição individual das variáveis

* **Random Forest Regressor**

  * Captura relações não-lineares e interações complexas

* **Gradient Boosting (XGBoost / LightGBM)**

  * Modelos de alto desempenho para capturar padrões e tendências temporais

---

## ⚠️ Observação

Este estudo é **estritamente observacional e exploratório**, não permitindo inferência causal direta.
