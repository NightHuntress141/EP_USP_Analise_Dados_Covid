# %%
# Pra mim (becky): conda activate icd_projeto
# conda env export > environment.yml
# conda env create -f environment.yml

# %% [markdown]
# # Importações

# %%
import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import plotly.graph_objects as dict_to_plotly
from plotly.subplots import make_subplots

import openpyxl
import joblib
from scipy import stats
import warnings
warnings.filterwarnings("ignore")

# %% [markdown]
# # Funções

# %%
def region(df):
    """
    Agrupa os estados por regiões
    """
    mapeamento_regioes = {
    # Região Norte
    'AM': 'Norte', 'PA': 'Norte', 'RO': 'Norte', 'RR': 'Norte', 'AC': 'Norte', 'AP': 'Norte', 'TO': 'Norte',
    
    # Região Nordeste
    'MA': 'Nordeste', 'PI': 'Nordeste', 'CE': 'Nordeste', 'RN': 'Nordeste', 'PB': 'Nordeste', 'PE': 'Nordeste', 
    'AL': 'Nordeste', 'SE': 'Nordeste', 'BA': 'Nordeste',
    
    # Região Centro-Oeste
    'MT': 'Centro-Oeste', 'MS': 'Centro-Oeste', 'GO': 'Centro-Oeste', 'DF': 'Centro-Oeste',
    
    # Região Sudeste
    'SP': 'Sudeste', 'RJ': 'Sudeste', 'MG': 'Sudeste', 'ES': 'Sudeste',
    
    # Região Sul
    'PR': 'Sul', 'RS': 'Sul', 'SC': 'Sul',
    
    # Caso especial do agregado nacional presente na base de dados
    'TOTAL': 'Nacional'
}

    df['region'] = df['state'].map(mapeamento_regioes)

    print("Sucesso: Coluna de regiões criada")
    return df

# %%
def classificar_onda(date):
    # Antes da vacinação em massa
    if date < pd.Timestamp('2021-01-17'):
        return '1_pre_vacinacao'
    # Predominância da Gamma (P.1)
    elif date < pd.Timestamp('2021-08-15'):
        return '2_gamma'
    # Predominância da Delta
    elif date < pd.Timestamp('2021-12-15'):
        return '3_delta'
    # Explosão e predominância da Omicron
    elif date < pd.Timestamp('2022-07-01'):
        return '4_omicron'
    # Queda após grandes ondas de transmissão
    else:
        return '5_pos_pico'

# %%
def aplicar_medias_moveis(df, colunas_alvo=['newCases', 'newDeaths'], janelas=[7, 15, 30]):
    """
    Faz a média móvel para as colunas de novos casos e mortes nas janelas de 7, 15 e 30 dias
    """
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(by=['state', 'date']).reset_index(drop=True)
    
    for coluna in colunas_alvo:
        for janela in janelas:
            nome_nova_coluna = f"{coluna}_mm{janela}"
            # Aplica o cálculo agrupado por estado
            df[nome_nova_coluna] = df.groupby('state')[coluna].transform(
                lambda x: x.rolling(window=janela, min_periods=1).mean()
            )
            
    print(f"Sucesso: Médias móveis aplicadas para as colunas {colunas_alvo} nas janelas {janelas}.")
    return df

# %%
def defasagem(df,colunas_alvo=['newCases'], lags=[7, 14, 21]):
    """
    Faz o cálculo da defasagem na coluna de novos casos para 7, 14 e 21 dias atrás
    """
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(by=['state', 'date']).reset_index(drop=True)

    for coluna in colunas_alvo:
        for lag in lags:
            nome_nova_coluna = f"{coluna}_lag{lag}"
            # O .shift(lag) move os dados daquela coluna 'X' dias para a frente
            df[nome_nova_coluna] = df.groupby('state')[coluna].shift(lag)
            
    print(f"Sucesso: Lags de {lags} dias aplicados para as colunas {colunas_alvo}.")
    return df

# %%
# =========================================================
# LAG EPIDEMIOLÓGICO GLOBAL — COVID
# =========================================================

def encontrar_lag_ideal_global(
    df,
    estados=None,
    max_lag=40,
    min_lag=5,
    coluna_casos='newCases',
    coluna_obitos='newDeaths',
    remover_estados_ruidosos=True
):
    """
    Descobre o lag epidemiológico ideal entre CASOS e ÓBITOS.

    Metodologia:
    -------------
    ✓ Cross-correlation temporal
    ✓ Suavização epidemiológica robusta
    ✓ Normalização Z-score
    ✓ Correlação temporal real
    ✓ Resultado individual por estado
    ✓ Resultado médio nacional

    Interpretação:
    --------------
    Mede o atraso médio entre:
        aumento de casos -> aumento de óbitos
    """

    # =====================================================
    # CÓPIA E LIMPEZA
    # =====================================================

    df = df.copy()

    # Remove agregado nacional
    df = df[df['state'] != 'TOTAL']

    # Remove estados muito pequenos/ruidosos
    if remover_estados_ruidosos:

        estados_ruidosos = ['RR', 'AP', 'AC']

        df = df[~df['state'].isin(estados_ruidosos)]

    # Estados analisados
    if estados is None:

        estados = sorted(df['state'].unique())

    # =====================================================
    # ESTRUTURAS
    # =====================================================

    resultados_estados = []

    correlacoes_por_lag = {
        lag: [] for lag in range(max_lag + 1)
    }

    # =====================================================
    # LOOP DOS ESTADOS
    # =====================================================

    for estado in estados:

        df_estado = (
            df[df['state'] == estado]
            .sort_values('date')
            .copy()
        )

        # =================================================
        # SÉRIES TEMPORAIS
        # =================================================

        casos = df_estado[coluna_casos].astype(float)
        obitos = df_estado[coluna_obitos].astype(float)

        # Remove negativos/anomalias
        casos = casos.clip(lower=0)
        obitos = obitos.clip(lower=0)

        # =================================================
        # SUAVIZAÇÃO EPIDEMIOLÓGICA
        # =================================================
        # 14 dias preserva o lag real
        # e reduz ruído administrativo

        casos = casos.rolling(
            window=14,
            center=True
        ).mean()

        obitos = obitos.rolling(
            window=14,
            center=True
        ).mean()

        # =================================================
        # REMOVE NaNs
        # =================================================

        serie = pd.DataFrame({
            'casos': casos,
            'obitos': obitos
        }).dropna()

        casos = serie['casos']
        obitos = serie['obitos']

        # =================================================
        # NORMALIZAÇÃO Z-SCORE
        # =================================================

        casos = (
            (casos - casos.mean())
            / casos.std()
        )

        obitos = (
            (obitos - obitos.mean())
            / obitos.std()
        )

        # =================================================
        # TESTE DOS LAGS
        # =================================================

        correlacoes = []

        for lag in range(max_lag + 1):

            casos_lag = casos.shift(lag)

            temp = pd.DataFrame({
                'obitos': obitos,
                'casos_lag': casos_lag
            }).dropna()

            # Dados insuficientes
            if len(temp) < 30:

                correlacao = np.nan

            else:

                correlacao = temp['obitos'].corr(
                    temp['casos_lag']
                )

            correlacoes.append(correlacao)

            correlacoes_por_lag[lag].append(correlacao)

        # =================================================
        # IGNORA LAGS BIOLOGICAMENTE IMPOSSÍVEIS
        # =================================================

        lags_validos = range(min_lag, max_lag + 1)

        corr_validas = [
            correlacoes[i]
            for i in lags_validos
        ]

        if np.all(np.isnan(corr_validas)):
            continue

        idx_local = np.nanargmax(corr_validas)

        lag_ideal = list(lags_validos)[idx_local]

        corr_ideal = corr_validas[idx_local]

        # =================================================
        # RESULTADO DO ESTADO
        # =================================================

        resultados_estados.append({
            'Estado': estado,
            'Lag Ideal': lag_ideal,
            'Correlação': round(corr_ideal, 4)
        })

    # =====================================================
    # RESULTADOS ESTADUAIS
    # =====================================================

    df_resultados = (
        pd.DataFrame(resultados_estados)
        .sort_values('Lag Ideal')
        .reset_index(drop=True)
    )

    # =====================================================
    # MÉDIA GLOBAL DOS LAGS
    # =====================================================

    medias_globais = []

    for lag in range(max_lag + 1):

        valores = correlacoes_por_lag[lag]

        media = np.nanmean(valores)

        medias_globais.append(media)

    df_media = pd.DataFrame({
        'Lag': range(max_lag + 1),
        'Correlação Média': medias_globais
    })

    # =====================================================
    # MELHOR LAG GLOBAL
    # =====================================================

    df_media_filtrado = df_media[
        df_media['Lag'] >= min_lag
    ]

    idx_global = (
        df_media_filtrado['Correlação Média']
        .idxmax()
    )

    lag_global = int(
        df_media.loc[idx_global, 'Lag']
    )

    corr_global = float(
        df_media.loc[idx_global, 'Correlação Média']
    )

    # =====================================================
    # PRINT DOS RESULTADOS
    # =====================================================

    print("\n============================================")
    print("LAG IDEAL POR ESTADO")
    print("============================================\n")

    print(df_resultados.to_string(index=False))

    print("\n============================================")
    print(f"LAG IDEAL GLOBAL: {lag_global} dias")
    print(f"CORRELAÇÃO MÉDIA: {corr_global:.4f}")
    print("============================================")

    # =====================================================
    # GRÁFICO
    # =====================================================

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df_media['Lag'],
            y=df_media['Correlação Média'],
            mode='lines+markers',
            line=dict(width=3),
            name='Correlação Média'
        )
    )

    # Região epidemiológica esperada
    fig.add_vrect(
        x0=10,
        x1=25,
        fillcolor="green",
        opacity=0.08,
        line_width=0,
        annotation_text="Faixa epidemiológica esperada"
    )

    # Lag ideal
    fig.add_vline(
        x=lag_global,
        line_dash='dash',
        line_color='red',
        annotation_text=f'Lag Ideal = {lag_global} dias'
    )

    fig.update_layout(
        title=(
            '<b>Correlação Cruzada — Casos x Óbitos</b>'
            '<br>Lag Epidemiológico Médio Brasileiro'
        ),
        xaxis_title='Lag (dias)',
        yaxis_title='Correlação Média',
        template='plotly_white',
        width=1000,
        height=550
    )

    fig.show()

    return {
        'lag_global': lag_global,
        'correlacao_global': corr_global,
        'lags_estaduais': df_resultados,
        'media_lags': df_media
    }

# %% [markdown]
# # Amostragem

# %%
data = pd.read_csv(r"..\data\raw\cases-brazil-states.csv")

# %%
data.info()

# %%
# Divisão em uma faixa trimestral pelo conjunto estado-periodo
data['date'] = pd.to_datetime(data['date'])
data['periodo_temporal'] = data['date'].dt.to_period('Q')

# %%
# Estrato através do cruzamento entre Estado (state) e Período Temporal
data['estrato'] = data['state'].astype(str) + "_" + data['periodo_temporal'].astype(str)

# %%
# Amostragem de 30%
sub = data.groupby('estrato', group_keys=False).sample(frac=0.3, random_state=42)
print(f"Tamanho da subamostra obtida (30%): {sub.shape[0]} linhas.")

# %%
sub.tail(10)

# %% [markdown]
# # Tratamento

# %%
# Drop das colunas que não agregam informações relevantes: Pais analisado (todos são Brasil), cidade (todas do estado) e a semana da analise
sub = sub.drop(columns=['country', 'city', 'epi_week'])

# %%
sub = sub.sort_values(by=['state', 'date']).reset_index(drop=True)

# %%
# Verificar duplicadas
sub.duplicated().sum()

# %%
# Retirar os NaN
sub.fillna(0, inplace=True)

# %% [markdown]
# ### Criação de Variáveis derivadas

# %%
sub = region(sub)

# %%
sub = aplicar_medias_moveis(sub)

# %%
sub['taxa_letalidade'] = sub['deaths_by_totalCases'] * 100
sub_estados = sub[sub['state'] != 'TOTAL'].copy()

# %%
sub['onda'] = sub['date'].apply(classificar_onda)

# %%
resultado_lag = encontrar_lag_ideal_global(
    sub,
    max_lag=40,
    min_lag=5
)

# %%
for estado in ['SP', 'AM', 'CE', 'RS', 'GO']:
    lag = encontrar_lag_ideal(sub_estados, estado=estado)
    print(f"{estado}: lag ideal = {lag} dias")

# %%
sub = defasagem(sub, colunas_alvo=['newCases'], lags=[7, 14, 21])
sub = defasagem(sub, colunas_alvo=['newDeaths'], lags=[7, 14, 21])

# %%
sub.shape

# %%
sub.info()

# %%
data = region(data)
data['region'].value_counts(normalize=True)

# %%
sub['region'].value_counts(normalize=True)

# %%
print(data['date'].min())
print(sub['date'].min())

# %%
print(data['date'].max())
print(sub['date'].max())

# %% [markdown]
# # Exploratória

# %%
variaveis_foco = [
    'newDeaths',
    'deaths',
    'newCases',
    'totalCases',
    'deathsMS',
    'totalCasesMS',
    'deaths_per_100k_inhabitants',
    'totalCases_per_100k_inhabitants',
    'deaths_by_totalCases',
    'recovered',
    'suspects',
    'tests',
    'tests_per_100k_inhabitants',
    'vaccinated',
    'vaccinated_per_100_inhabitants',
    'vaccinated_second',
    'vaccinated_second_per_100_inhabitants',
    'vaccinated_single',
    'vaccinated_single_per_100_inhabitants',
    'vaccinated_third',
    'vaccinated_third_per_100_inhabitants',
    'newCases_mm7',
    'newCases_mm15',
    'newCases_mm30',
    'newDeaths_mm7',
    'newDeaths_mm15',
    'newDeaths_mm30'
]

sub_estados[variaveis_foco].describe().T.round(3)

# %% [markdown]
# ## 1 — Série Temporal: Casos e Óbitos por Estado

# %%
def plot_serie_temporal_casos_obitos(df, estados=None, altura=650):
    """
    Série temporal (linhas) de novos casos e novos óbitos por estado,
    usando médias móveis de 7 dias para suavizar ruídos.

    Parâmetros
    ----------
    df      : DataFrame com 'state', 'date', 'newCases_mm7', 'newDeaths_mm7'
    estados : lista de siglas; se None, usa os 5 maiores em casos totais
    altura  : altura do gráfico em pixels
    """
    if estados is None:
        estados = (
            df.groupby('state')['totalCases'].max()
            .nlargest(5).index.tolist()
        )

    df_plot = df[df['state'].isin(estados)].sort_values('date')
    palette = px.colors.qualitative.Plotly

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        subplot_titles=(
            '<b>Novos Casos</b> — Média Móvel 7 dias',
            '<b>Novos Óbitos</b> — Média Móvel 7 dias'
        ),
        vertical_spacing=0.10
    )

    for i, estado in enumerate(estados):
        df_e = df_plot[df_plot['state'] == estado]
        cor  = palette[i % len(palette)]

        fig.add_trace(
            go.Scatter(
                x=df_e['date'], y=df_e['newCases_mm7'],
                name=estado, mode='lines',
                line=dict(color=cor, width=2),
                legendgroup=estado,
            ),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=df_e['date'], y=df_e['newDeaths_mm7'],
                name=estado, mode='lines',
                line=dict(color=cor, width=2, dash='dot'),
                legendgroup=estado,
                showlegend=False,
            ),
            row=2, col=1
        )

    fig.update_layout(
        title='<b>Série Temporal — Novos Casos e Óbitos por Estado</b>',
        title_font_size=18,
        hovermode='x unified',
        template='plotly_white',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
        height=altura,
    )
    fig.update_xaxes(title_text='Data', row=2, col=1)
    fig.update_yaxes(title_text='Novos Casos (MM7)',  row=1, col=1)
    fig.update_yaxes(title_text='Novos Óbitos (MM7)', row=2, col=1)

    datas_vacinacao = [
        ("1ª Onda", "2021-01-16", "green"),
        ("2ª Onda", "2021-07-01", "orange"),
        ("3ª Onda", "2021-09-15", "red"),
    ]

    for nome, data, cor in datas_vacinacao:
        fig.add_vline(
            x=data,
            line_width=2,
            line_dash="dash",
            line_color=cor
        )

        fig.add_annotation(
            x=data,
            y=0.98,
            yref="paper",
            text=f"<b>{nome}</b>",
            showarrow=False,
            xanchor="left",
            bgcolor="white",
            bordercolor=cor,
            borderwidth=1,
            font=dict(color=cor, size=11)
        )

    ondas = [
        ("Pré-vacinação", "2020-02-26", "black"),
        ("Gamma",         "2021-01-17", "purple"),
        ("Delta",         "2021-08-15", "blue"),
        ("Ômicron",       "2021-12-15", "red"),
        ("Pós-pico",      "2022-07-01", "green"),
    ]

    for nome, data, cor in ondas:
            fig.add_vline(
                x=data,
                line_color=cor,
                line_dash="dot",
                line_width=2
            )

            fig.add_annotation(
                x=data,
                y=1.06,
                yref="paper",
                text=f"<b>{nome}</b>",
                showarrow=False,
                xanchor="left",
                font=dict(size=10, color=cor)
            )

    fig.show()


plot_serie_temporal_casos_obitos(sub_estados)


# %% [markdown]
# ## 2 — Série Temporal: Vacinação por Estado

# %%
def plot_serie_temporal_vacinacao(df, estados=None, altura=550):
    """
    Série temporal do avanço da vacinação (% da população com 1ª dose)
    por estado, sobreposta à curva de óbitos (MM7) para evidenciar correlação.

    Usa a coluna já existente 'vaccinated_per_100_inhabitants' (porcentagem).

    Parâmetros
    ----------
    df      : DataFrame com 'state', 'date', 'vaccinated_per_100_inhabitants', 'newDeaths_mm7'
    estados : lista de siglas; se None, usa os 5 com maior cobertura vacinal final
    altura  : altura do gráfico em pixels
    """
    if estados is None:
        estados = (
            df.groupby('state')['vaccinated_per_100_inhabitants'].max()
            .nlargest(5).index.tolist()
        )

    df_plot  = df[df['state'].isin(estados)].sort_values('date')
    palette  = px.colors.qualitative.Safe

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    for i, estado in enumerate(estados):
        df_e = df_plot[df_plot['state'] == estado]
        cor  = palette[i % len(palette)]

        # Vacinação — 1ª dose (%) — eixo primário
        fig.add_trace(
            go.Scatter(
                x=df_e['date'], y=df_e['vaccinated_per_100_inhabitants'],
                name=f'{estado} — 1ª Dose (%)',
                mode='lines',
                line=dict(color=cor, width=2),
                legendgroup=estado,
            ),
            secondary_y=False
        )
        # Óbitos MM7 — eixo secundário, tracejado
        fig.add_trace(
            go.Scatter(
                x=df_e['date'], y=df_e['newDeaths_mm7'],
                name=f'{estado} — Óbitos',
                mode='lines',
                line=dict(color=cor, width=1.5, dash='dash'),
                legendgroup=estado,
                showlegend=False,
                opacity=0.6,
            ),
            secondary_y=True
        )

    fig.update_layout(
        title='<b>Série Temporal — Vacinação (1ª Dose %) e Óbitos por Estado</b>',
        title_font_size=18,
        hovermode='x unified',
        template='plotly_white',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
        height=altura,
    )
    fig.update_xaxes(title_text='Data')
    fig.update_yaxes(title_text='<b>1ª Dose (% pop.)</b>',    color='SteelBlue', secondary_y=False)
    fig.update_yaxes(title_text='<b>Novos Óbitos (MM7)</b>',  color='Crimson',   secondary_y=True)
    fig.show()


plot_serie_temporal_vacinacao(sub_estados)


# %% [markdown]
# ## 3 — Mapa Coroplético: Mortalidade por Estado

# %%
def plot_mapa_coropletico(df, altura=600):
    """
    Mapa coroplético do Brasil colorindo cada estado pela taxa de óbitos
    por 100 mil habitantes.

    Usa a coluna já existente 'deaths_per_100k_inhabitants'.

    Parâmetros
    ----------
    df    : DataFrame com 'state', 'deaths_per_100k_inhabitants'
    altura: altura do mapa em pixels
    """
    # Snapshot: valor máximo acumulado por estado
    df_mapa = (
        df.groupby('state')['deaths_per_100k_inhabitants']
        .max()
        .reset_index()
    )

    fig = px.choropleth(
        df_mapa,
        geojson='https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson',
        locations='state',
        featureidkey='properties.sigla',
        color='deaths_per_100k_inhabitants',
        color_continuous_scale='Reds',
        range_color=(
            df_mapa['deaths_per_100k_inhabitants'].min(),
            df_mapa['deaths_per_100k_inhabitants'].max()
        ),
        labels={'deaths_per_100k_inhabitants': 'Óbitos / 100k hab.'},
        title='<b>Mortalidade por COVID-19 — Óbitos por 100 mil Habitantes</b>',
    )

    fig.update_geos(fitbounds='locations', visible=False, bgcolor='rgba(0,0,0,0)')
    fig.update_layout(
        template='plotly_white',
        height=altura,
        coloraxis_colorbar=dict(
            title='Óbitos<br>/ 100k hab.',
            thicknessmode='pixels', thickness=18,
            lenmode='fraction', len=0.75,
        ),
        margin=dict(l=0, r=0, t=60, b=0),
    )
    fig.show()


plot_mapa_coropletico(sub_estados)


# %% [markdown]
# ## 4 — Boxplot: Mortalidade por Região

# %%
def plot_boxplot_regiao(df, altura=550):
    """
    Boxplot comparando a distribuição de óbitos por 100 mil habitantes
    entre as cinco regiões geográficas do Brasil.

    Usa a coluna já existente 'deaths_per_100k_inhabitants'.

    Parâmetros
    ----------
    df    : DataFrame com 'region', 'deaths_per_100k_inhabitants'
    altura: altura do gráfico em pixels
    """
    df_plot = df.dropna(subset=['deaths_per_100k_inhabitants', 'region'])

    ordem_regioes = ['Norte', 'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul']
    palette = {
        'Norte':        '#1f77b4',
        'Nordeste':     '#ff7f0e',
        'Centro-Oeste': '#2ca02c',
        'Sudeste':      '#d62728',
        'Sul':          '#9467bd',
    }

    fig = go.Figure()
    for regiao in ordem_regioes:
        df_r = df_plot[df_plot['region'] == regiao]
        fig.add_trace(
            go.Box(
                y=df_r['deaths_per_100k_inhabitants'],
                name=regiao,
                boxpoints='outliers',
                marker_color=palette.get(regiao, 'gray'),
                line_color=palette.get(regiao, 'gray'),
                fillcolor=palette.get(regiao, 'gray'),
                opacity=0.7,
            )
        )

    fig.update_layout(
        title='<b>Distribuição de Mortalidade por Região</b><br>Óbitos por 100k hab.',
        title_font_size=18,
        yaxis_title='Óbitos por 100k habitantes',
        xaxis_title='Região',
        template='plotly_white',
        showlegend=False,
        height=altura,
    )
    fig.show()


plot_boxplot_regiao(sub_estados)


# %% [markdown]
# ## 5 — Scatter Plot: Cobertura Vacinal × Mortalidade

# %%
def plot_scatter_vacina_obito(df, altura=600):
    """
    Scatter plot explorando a correlação entre cobertura da 2ª dose (%) e
    óbitos acumulados por 100k hab., com linha de tendência OLS,
    colorido por região e dimensionado pelo total de casos.

    Usa as colunas já existentes:
        'vaccinated_second_per_100_inhabitants' (% 2ª dose)
        'deaths_per_100k_inhabitants'

    Parâmetros
    ----------
    df    : DataFrame — usa snapshot da última data por estado
    altura: altura do gráfico em pixels
    """
    df_snap = (
        df.sort_values('date')
        .groupby('state')
        .last()
        .reset_index()
        .dropna(subset=['vaccinated_second_per_100_inhabitants', 'deaths_per_100k_inhabitants'])
    )

    # Remove zeros que distorceriam a correlação (estados sem dado de vacina)
    df_snap = df_snap[
        (df_snap['vaccinated_second_per_100_inhabitants'] > 0) &
        (df_snap['deaths_per_100k_inhabitants'] > 0)
    ]

    r, p = stats.pearsonr(
        df_snap['vaccinated_second_per_100_inhabitants'],
        df_snap['deaths_per_100k_inhabitants']
    )

    # Linha de tendência manual com numpy (sem statsmodels)
    x_vals = df_snap['vaccinated_second_per_100_inhabitants'].values
    y_vals = df_snap['deaths_per_100k_inhabitants'].values
    coef   = np.polyfit(x_vals, y_vals, 1)
    x_line = np.linspace(x_vals.min(), x_vals.max(), 200)
    y_line = np.polyval(coef, x_line)

    fig = px.scatter(
        df_snap,
        x='vaccinated_second_per_100_inhabitants',
        y='deaths_per_100k_inhabitants',
        color='region',
        size='totalCases',
        text='state',
        labels={
            'vaccinated_second_per_100_inhabitants': '2ª Dose (% da população)',
            'deaths_per_100k_inhabitants':           'Óbitos por 100k hab.',
            'region':                                'Região',
        },
        title=(
            f'<b>Cobertura Vacinal (2ª Dose) × Mortalidade por Estado</b>'
            f'<br>r de Pearson = {r:.3f}  |  p-valor = {p:.4f}'
        ),
        color_discrete_sequence=px.colors.qualitative.Safe,
        template='plotly_white',
        height=altura,
    )
    fig.update_traces(
        textposition='top center',
        selector=dict(mode='markers+text')
    )
    # Adiciona a reta de tendência manualmente
    fig.add_trace(
        go.Scatter(
            x=x_line, y=y_line,
            mode='lines',
            name=f'Tendência (y = {coef[0]:.2f}x + {coef[1]:.1f})',
            line=dict(color='black', width=2, dash='dash'),
            showlegend=True,
        )
    )
    fig.update_layout(
        title_font_size=17,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
    )
    fig.show()


plot_scatter_vacina_obito(sub_estados)


# %% [markdown]
# ## 6 — Heatmap de Correlação: Todas as Variáveis Numéricas

# %%
def plot_heatmap_correlacao(df, altura=800):
    """
    Heatmap da matriz de correlação de Pearson entre todas as variáveis
    numéricas, útil para detectar multicolinearidade antes da modelagem.
    Exibe apenas o triângulo inferior para evitar redundância.

    Parâmetros
    ----------
    df    : DataFrame completo (sub_estados)
    altura: altura do gráfico em pixels
    """
    # Exclui colunas puramente identificadoras ou derivadas de índice
    colunas_excluir = ['epi_week']
    numericas = df.select_dtypes(include='number').drop(
        columns=[c for c in colunas_excluir if c in df.columns],
        errors='ignore'
    )

    corr = numericas.corr(method='pearson').round(2)

    # Máscara triangular superior
    mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
    corr_lower = corr.where(~mask)

    fig = go.Figure(
        go.Heatmap(
            z=corr_lower.values,
            x=corr_lower.columns.tolist(),
            y=corr_lower.index.tolist(),
            colorscale='RdBu_r',
            zmid=0, zmin=-1, zmax=1,
            text=corr_lower.round(2).values,
            texttemplate='%{text}',
            textfont=dict(size=8),
            colorbar=dict(title='r de<br>Pearson'),
            hoverongaps=False,
        )
    )
    fig.update_layout(
        title='<b>Heatmap de Correlação — Variáveis Numéricas</b>',
        title_font_size=18,
        template='plotly_white',
        height=altura,
        xaxis=dict(tickangle=-45),
        margin=dict(l=180, b=180),
    )
    fig.show()


plot_heatmap_correlacao(sub_estados)


# %% [markdown]
# ## 7 — Gráfico de Barras: Ranking de Letalidade por Estado

# %%
def plot_barras_letalidade(df, altura=620):
    """
    Gráfico de barras horizontais com o ranking de taxa de letalidade
    por estado, ordenado do maior para o menor.

    Usa a coluna derivada 'taxa_letalidade' (deaths_by_totalCases × 100),
    calculada na célula de preparação.

    Parâmetros
    ----------
    df    : DataFrame com 'state', 'taxa_letalidade', 'region'
    altura: altura do gráfico em pixels
    """
    # Snapshot: última data disponível por estado
    df_snap = (
        df.sort_values('date')
        .groupby('state')
        .last()
        .reset_index()
        .dropna(subset=['taxa_letalidade'])
        .sort_values('taxa_letalidade', ascending=True)  # crescente → barras ordenadas
    )

    mapa_cores = {
        'Norte':        '#1f77b4',
        'Nordeste':     '#ff7f0e',
        'Centro-Oeste': '#2ca02c',
        'Sudeste':      '#d62728',
        'Sul':          '#9467bd',
    }
    cores = df_snap['region'].map(mapa_cores).fillna('#aec7e8').tolist()

    fig = go.Figure(
        go.Bar(
            x=df_snap['taxa_letalidade'],
            y=df_snap['state'],
            orientation='h',
            marker_color=cores,
            text=df_snap['taxa_letalidade'].map('{:.2f}%'.format),
            textposition='outside',
            hovertemplate='%{y}: %{x:.2f}%<extra></extra>',
        )
    )

    media = df_snap['taxa_letalidade'].mean()
    fig.add_vline(
        x=media, line_dash='dash', line_color='black',
        annotation_text=f'Média: {media:.2f}%',
        annotation_position='top right',
    )

    # Legenda manual por região
    for regiao, cor in mapa_cores.items():
        fig.add_trace(
            go.Bar(x=[None], y=[None], marker_color=cor, name=regiao, showlegend=True)
        )

    fig.update_layout(
        title='<b>Ranking de Letalidade por Estado</b><br>Taxa = (Óbitos Totais / Casos Totais) × 100',
        title_font_size=18,
        xaxis_title='Taxa de Letalidade (%)',
        yaxis_title='Estado',
        template='plotly_white',
        height=altura,
        margin=dict(r=90),
        barmode='overlay',
        legend=dict(
            title='Região',
            orientation='v',
            yanchor='bottom', y=0.01,
            xanchor='right',  x=0.99,
        ),
    )
    fig.show()


plot_barras_letalidade(sub_estados)


# %%



