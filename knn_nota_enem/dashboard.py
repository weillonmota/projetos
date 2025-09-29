# ===================================================================
# 1. IMPORTAÇÕES E CONFIGURAÇÃO DA PÁGINA
# ===================================================================
import streamlit as st
import pandas as pd
import joblib
import json
import plotly.express as px
import plotly.figure_factory as ff
import numpy as np

st.set_page_config(layout="wide", page_title="Dashboard ENEM - Ceará")

# ===================================================================
# 2. CONSTANTES E DICIONÁRIOS
# ===================================================================
# (Esta seção permanece inalterada)
MAPA_RENDA = {
    'Nenhuma Renda': 'A', 'Até R$ 1.320,00': 'B', 'De R$ 1.320,01 até R$ 1.980,00': 'C',
    'De R$ 1.980,01 até R$ 2.640,00': 'D', 'De R$ 2.640,01 até R$ 3.300,00': 'E',
    'De R$ 3.300,01 até R$ 3.960,00': 'F', 'De R$ 3.960,01 até R$ 5.280,00': 'G',
    'De R$ 5.280,01 até R$ 6.600,00': 'H', 'De R$ 6.600,01 até R$ 7.920,00': 'I',
    'De R$ 7.920,01 até R$ 9.240,00': 'J', 'De R$ 9.240,01 até R$ 10.560,00': 'K',
    'De R$ 10.560,01 até R$ 11.880,00': 'L', 'De R$ 11.880,01 até R$ 13.200,00': 'M',
    'De R$ 13.200,01 até R$ 15.840,00': 'N', 'De R$ 15.840,01 até R$ 19.800,00': 'O',
    'De R$ 19.800,01 até R$ 26.400,00': 'P', 'Acima de R$ 26.400,00': 'Q'
}
MAPA_ESCOLARIDADE_MAE = {
    'Nunca estudou': 'A', 'Não completou a 4ª série/5º ano do Ensino Fundamental': 'B',
    'Completou a 4ª série/5º ano, mas não completou a 8ª série/9º ano': 'C',
    'Completou a 8ª série/9º ano, mas não completou o Ensino Médio': 'D',
    'Completou o Ensino Médio, mas não completou a Faculdade': 'E',
    'Completou a Faculdade, mas não completou a Pós-graduação': 'F',
    'Completou a Pós-graduação': 'G', 'Não sei': 'H'
}
MAPA_TIPO_ESCOLA = {'Pública': 2, 'Privada': 3}
MAPA_COR_RACA = {
    'Parda': 3, 'Branca': 1, 'Preta': 2, 'Amarela': 4, 'Indígena': 5,
    'Não declarado': 0, 'Não dispõe da informação': 6
}

# ===================================================================
# 3. FUNÇÕES DE CARREGAMENTO
# ===================================================================
# (Esta seção permanece inalterada)
@st.cache_resource
def carregar_modelo_e_colunas():
    try:
        modelo = joblib.load('modelo_knn.joblib')
        with open('colunas_modelo.json', 'r') as f:
            colunas = json.load(f)
        return modelo, colunas
    except FileNotFoundError:
        return None, None

@st.cache_data
def carregar_dados_ceara():
    try:
        return pd.read_csv('dados_ceara.csv')
    except FileNotFoundError:
        return None

# ===================================================================
# 4. FUNÇÕES DAS ABAS 
# ===================================================================
def aba_analise_exploratoria(df):
    st.header('Análise dos Dados Históricos do ENEM no Ceará')
    
    col1, col2 = st.columns(2)
    #... (métricas inalteradas)
    with col1:
        st.metric("Total de Participantes", f"{df.shape[0]:,}".replace(",", "."))
        st.metric("Média de Ciências da Natureza", f"{df['NU_NOTA_CN'].mean():.2f}")
        st.metric("Média de Matemática", f"{df['NU_NOTA_MT'].mean():.2f}")
    with col2:
        st.metric("Média de Ciências Humanas", f"{df['NU_NOTA_CH'].mean():.2f}")
        st.metric("Média de Linguagens e Códigos", f"{df['NU_NOTA_LC'].mean():.2f}")
        st.metric("Média da Redação", f"{df['NU_NOTA_REDACAO'].mean():.2f}")
        
    st.markdown("---")
    
    st.sidebar.header("Filtros para Análise")
    #... (filtros inalterados)
    tipo_escola_filtro = st.sidebar.multiselect(
        'Selecione o Tipo de Escola:', options=df['TP_ESCOLA'].unique(), default=df['TP_ESCOLA'].unique(),
        format_func=lambda x: {2: 'Pública', 3: 'Privada'}.get(x, 'Outro')
    )
    df_filtrado = df.query("TP_ESCOLA in @tipo_escola_filtro")
    st.subheader('Distribuição das Notas')
    materia_selecionada = st.selectbox(
        'Selecione a matéria:', options=['NU_NOTA_MT', 'NU_NOTA_REDACAO', 'NU_NOTA_CN', 'NU_NOTA_CH', 'NU_NOTA_LC'],
        format_func=lambda x: x.replace("NU_NOTA_", "").replace("REDACAO", "REDAÇÃO").replace("MT", "MATEMÁTICA").replace("CN", "CIÊNCIAS DA NATUREZA").replace("CH", "CIÊNCIAS HUMANAS").replace("LC", "LINGUAGENS E CÓDIGOS")
    )

    if not df_filtrado.empty:
        df_para_grafico = df_filtrado.sample(min(len(df_filtrado), 20000), random_state=42)
        media = df_filtrado[materia_selecionada].mean()
        mediana = df_filtrado[materia_selecionada].median()
        nome_materia = materia_selecionada.replace("NU_NOTA_", "").replace("REDACAO", "REDAÇÃO")
        
        fig = ff.create_distplot([df_para_grafico[materia_selecionada].dropna()], [nome_materia], show_hist=False, show_rug=False, colors=['#1f77b4'])
        fig.add_vline(x=media, line_width=3, line_dash="dash", line_color="red")
        fig.add_vline(x=mediana, line_width=3, line_dash="dot", line_color="green")
        
        # --- ALTERAÇÃO AQUI: Melhorando o layout do gráfico ---
        fig.update_layout(
            title_text=f'Curva de Densidade das Notas de {nome_materia}',
            xaxis_title="Nota",      # Adiciona título ao eixo X
            yaxis_title="Densidade", # Adiciona título ao eixo Y
            plot_bgcolor='white',    # Define o fundo do gráfico como branco
            xaxis_showgrid=False,    # Remove as linhas de grade do eixo X
            yaxis_showgrid=False,    # Remove as linhas de grade do eixo Y
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

        stat_col1, stat_col2 = st.columns(2)
        with stat_col1:
            st.metric(label="🔴 Média da Amostra", value=f"{media:.2f}")
        with stat_col2:
            st.metric(label="🟢 Mediana da Amostra", value=f"{mediana:.2f}")
    else:
        st.warning("Nenhum dado disponível para os filtros selecionados.")

def aba_previsao_notas(modelo, colunas):
    # (Esta função permanece inalterada)
    st.header('Preveja a Nota de um Novo Aluno')
    with st.form("prediction_form"):
        st.markdown("**Insira os dados socioeconômicos do aluno:**")
        col1, col2 = st.columns(2)
        with col1:
            renda = st.selectbox("Renda mensal da família:", options=list(MAPA_RENDA.keys()))
            escolaridade_mae = st.selectbox("Escolaridade da mãe:", options=list(MAPA_ESCOLARIDADE_MAE.keys()))
        with col2:
            tipo_escola = st.selectbox("Tipo de escola no Ens. Médio:", options=list(MAPA_TIPO_ESCOLA.keys()))
            cor_raca = st.selectbox("Como você se autodeclara?", options=list(MAPA_COR_RACA.keys()))
        submit_button = st.form_submit_button("✨ Prever Notas")
    if submit_button:
        dados_usuario = {'Q006': MAPA_RENDA[renda], 'Q002': MAPA_ESCOLARIDADE_MAE[escolaridade_mae], 'TP_ESCOLA': MAPA_TIPO_ESCOLA[tipo_escola], 'TP_COR_RACA': MAPA_COR_RACA[cor_raca], 'SG_UF_ESC': 'CE'}
        input_df = pd.DataFrame([dados_usuario])
        input_encoded = pd.get_dummies(input_df)
        final_input = input_encoded.reindex(columns=colunas, fill_value=0)
        with st.spinner("Analisando perfil e calculando..."):
            previsao = modelo.predict(final_input)
            media_geral = np.mean(previsao[0])
        st.success("Previsão Concluída!")
        st.subheader("Resultados Estimados:")
        st.metric(label="**Média Geral Prevista**", value=f"{media_geral:.2f}")
        st.markdown("---")
        df_resultados = pd.DataFrame({'Prova': ['Ciências da Natureza', 'Ciências Humanas', 'Linguagens e Códigos', 'Matemática', 'Redação'], 'Nota Estimada': previsao[0]})
        fig = px.bar(df_resultados, x='Prova', y='Nota Estimada', title='Distribuição das Notas Previstas', text=df_resultados['Nota Estimada'].apply(lambda x: f'{x:.2f}'), color='Prova', range_y=[0, 1000])
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

# ===================================================================
# 5. EXECUÇÃO PRINCIPAL DO DASHBOARD
# ===================================================================
st.title('Dashboard de Análise e Previsão ENEM 2021 a 2023 - Ceará')

modelo_knn, colunas_modelo = carregar_modelo_e_colunas()
df_ceara = carregar_dados_ceara()

if df_ceara is None or modelo_knn is None:
    st.error("Arquivos de dados ou do modelo não foram encontrados. Execute o notebook de ETL e treinamento primeiro.")
    st.stop()

tab1, tab2 = st.tabs(["📊 Análise Exploratória", "🤖 Previsão de Notas"])
with tab1:
    aba_analise_exploratoria(df_ceara)
with tab2:
    aba_previsao_notas(modelo_knn, colunas_modelo)