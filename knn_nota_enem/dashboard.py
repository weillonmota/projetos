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
import requests  # <-- Para baixar os arquivos
from pathlib import Path # <-- Para criar pastas e caminhos

# Configuração da página (deve ser o primeiro comando Streamlit)
st.set_page_config(layout="wide", page_title="Dashboard ENEM - Ceará")

# ===================================================================
# 2. CONSTANTES, URLs E CAMINHOS
# ===================================================================

# URLs dos seus 5 arquivos no GitHub Releases
# (Baseado no seu código antigo e na imagem da release)
BASE_URL = "https://github.com/weillonmota/projetos/releases/download/v1.0-dados/"
MODELO_URL = BASE_URL + "modelo_knn.joblib"
COLUNAS_URL = BASE_URL + "colunas_modelo.json"
DADOS_URL = BASE_URL + "dados_ceara.csv"
SCALER_URL = BASE_URL + "scaler.joblib"       # <-- ADICIONADO
Y_TRAIN_URL = BASE_URL + "y_train_data.csv"   # <-- ADICIONADO

# Caminhos locais onde os arquivos serão salvos temporariamente
PASTA_DADOS = Path("dados_app")
CAMINHO_MODELO = PASTA_DADOS / "modelo_knn.joblib"
CAMINHO_COLUNAS = PASTA_DADOS / "colunas_modelo.json"
CAMINHO_DADOS = PASTA_DADOS / "dados_ceara.csv"
CAMINHO_SCALER = PASTA_DADOS / "scaler.joblib"     # <-- ADICIONADO
CAMINHO_Y_TRAIN = PASTA_DADOS / "y_train_data.csv" # <-- ADICIONADO

# Dicionários de mapeamento (do seu código local)
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
NOMES_MATERIAS_DISPLAY = [
    'Ciências da Natureza', 'Ciências Humanas', 
    'Linguagens e Códigos', 'Matemática', 'Redação'
]

# ===================================================================
# 3. FUNÇÕES DE DOWNLOAD E CARREGAMENTO (MERGE)
# ===================================================================
def baixar_arquivo(url, caminho_destino):
    """Verifica se um arquivo existe, e se não, faz o download dele."""
    if not caminho_destino.exists():
        st.write(f"Baixando {caminho_destino.name}...")
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status() # Lança um erro para status HTTP ruins
            with open(caminho_destino, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        except requests.exceptions.RequestException as e:
            st.error(f"Erro ao baixar o arquivo {caminho_destino.name}: {e}")
            return False
    return True

@st.cache_resource
def carregar_artefatos_modelo():
    """
    Baixa e carrega os 4 artefatos do modelo: modelo, colunas, scaler e y_train.
    """
    # Baixa todos os 4 arquivos
    sucesso_modelo = baixar_arquivo(MODELO_URL, CAMINHO_MODELO)
    sucesso_colunas = baixar_arquivo(COLUNAS_URL, CAMINHO_COLUNAS)
    sucesso_scaler = baixar_arquivo(SCALER_URL, CAMINHO_SCALER)
    sucesso_y_train = baixar_arquivo(Y_TRAIN_URL, CAMINHO_Y_TRAIN)
    
    if sucesso_modelo and sucesso_colunas and sucesso_scaler and sucesso_y_train:
        try:
            modelo = joblib.load(CAMINHO_MODELO)
            scaler = joblib.load(CAMINHO_SCALER)
            with open(CAMINHO_COLUNAS, 'r') as f:
                colunas = json.load(f)
            y_train = pd.read_csv(CAMINHO_Y_TRAIN)
            return modelo, colunas, scaler, y_train
        except Exception as e:
            st.error(f"Erro ao carregar os artefatos do modelo: {e}")
            return None, None, None, None
    return None, None, None, None

@st.cache_data
def carregar_dados_ceara():
    """Baixa e carrega o CSV com os dados do Ceará."""
    if baixar_arquivo(DADOS_URL, CAMINHO_DADOS):
        try:
            return pd.read_csv(CAMINHO_DADOS)
        except Exception as e:
            st.error(f"Erro ao carregar o arquivo de dados: {e}")
            return None
    return None

# ===================================================================
# 4. FUNÇÕES DAS ABAS (DO SEU CÓDIGO LOCAL ATUALIZADO)
# ===================================================================

def aba_analise_exploratoria(df):
    st.header('Análise dos Dados Históricos do ENEM no Ceará')
    col1, col2 = st.columns(2)
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
        fig.update_layout(
            title_text=f'Curva de Densidade das Notas de {nome_materia}',
            xaxis_title="Nota", yaxis_title="Densidade",
            plot_bgcolor='white', xaxis_showgrid=False,
            yaxis_showgrid=False, showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
        stat_col1, stat_col2 = st.columns(2)
        with stat_col1:
            st.metric(label="🔴 Média da Amostra", value=f"{media:.2f}")
        with stat_col2:
            st.metric(label="🟢 Mediana da Amostra", value=f"{mediana:.2f}")
    else:
        st.warning("Nenhum dado disponível para os filtros selecionados.")


def formatar_comparacao(nota_prevista, serie_notas_vizinhos, k):
    """
    Compara a nota prevista (ponderada) com as notas dos vizinhos.
    """
    media_vizinhos = serie_notas_vizinhos.mean() 
    min_vizinhos = serie_notas_vizinhos.min()
    max_vizinhos = serie_notas_vizinhos.max()

    if nota_prevista < min_vizinhos:
        return (f"Sua nota prevista ({nota_prevista:.2f}) foi **menor** que a nota mais baixa ({min_vizinhos:.2f}) entre seus {k} vizinhos mais próximos."
                f" (A média simples deles foi {media_vizinhos:.2f})")
    elif nota_prevista > max_vizinhos:
        return (f"Sua nota prevista ({nota_prevista:.2f}) foi **maior** que a nota mais alta ({max_vizinhos:.2f}) entre seus {k} vizinhos mais próximos."
                f" (A média simples deles foi {media_vizinhos:.2f})")
    elif nota_prevista > media_vizinhos:
        return (f"Sua nota prevista ({nota_prevista:.2f}) está **acima** da média simples ({media_vizinhos:.2f}) dos seus {k} vizinhos."
                f" (As notas deles variaram de {min_vizinhos:.2f} a {max_vizinhos:.2f})")
    elif nota_prevista < media_vizinhos:
        return (f"Sua nota prevista ({nota_prevista:.2f}) está **abaixo** da média simples ({media_vizinhos:.2f}) dos seus {k} vizinhos."
                f" (As notas deles variaram de {min_vizinhos:.2f} a {max_vizinhos:.2f})")
    else: 
        return (f"Sua nota prevista ({nota_prevista:.2f}) é **igual** à média simples ({media_vizinhos:.2f}) dos seus {k} vizinhos."
                f" (As notas deles variaram de {min_vizinhos:.2f} a {max_vizinhos:.2f})")


def aba_previsao_notas(modelo, colunas, scaler, y_train):
    """
    Renderiza a aba de Previsão de Notas com todas as novas funcionalidades.
    """
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
        # 1. Prepara os dados do usuário
        dados_usuario = {
            'Q006': MAPA_RENDA[renda], 
            'Q002': MAPA_ESCOLARIDADE_MAE[escolaridade_mae], 
            'TP_ESCOLA': MAPA_TIPO_ESCOLA[tipo_escola], 
            'TP_COR_RACA': MAPA_COR_RACA[cor_raca], 
            'SG_UF_ESC': 'CE' 
        }
        input_df = pd.DataFrame([dados_usuario])
        input_encoded = pd.get_dummies(input_df)
        final_input = input_encoded.reindex(columns=colunas, fill_value=0)
        
        # 2. Aplica o StandardScaler (lido da internet)
        final_input_scaled = scaler.transform(final_input)
        
        with st.spinner("Analisando perfil e calculando..."):
            # 3. Faz a previsão (ponderada)
            previsao = modelo.predict(final_input_scaled)
            media_geral = np.mean(previsao[0])
            
            # 4. Encontra os vizinhos
            k_vizinhos = modelo.n_neighbors
            distancias, indices = modelo.kneighbors(final_input_scaled)
            
            # 5. Busca as notas desses vizinhos no y_train (lido da internet)
            vizinhos_indices = indices[0]
            vizinhos_df = y_train.iloc[vizinhos_indices]
            
            # 6. Prepara os textos de comparação
            comparacoes = []
            colunas_notas = y_train.columns.tolist() 
            
            for i, nome_display in enumerate(NOMES_MATERIAS_DISPLAY):
                col_nota = colunas_notas[i] 
                nota_aluno = previsao[0][i] 
                notas_vizinhos = vizinhos_df[col_nota]
                texto_comp = formatar_comparacao(nota_aluno, notas_vizinhos, k_vizinhos)
                comparacoes.append((nome_display, texto_comp))

        st.success("Previsão Concluída!")
        st.subheader("Resultados Estimados:")
        
        st.metric(label="**Média Geral Prevista**", value=f"{media_geral:.2f}")
        
        # Gráfico de barras com as notas
        df_resultados = pd.DataFrame({
            'Prova': NOMES_MATERIAS_DISPLAY,
            'Nota Estimada': previsao[0]
        })
        fig = px.bar(df_resultados, x='Prova', y='Nota Estimada', title='Distribuição das Notas Previstas', 
                     text=df_resultados['Nota Estimada'].apply(lambda x: f'{x:.2f}'), 
                     color='Prova', range_y=[0, 1000])
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
        # Exibe a comparação
        st.markdown("---")
        st.subheader(f"Comparação com os {k_vizinhos} Alunos de Perfil Similar")
        st.info(f"O modelo encontrou os {k_vizinhos} alunos da base de dados com perfil socioeconômico mais parecido com o seu. Sua nota prevista (calculada dando mais peso aos vizinhos mais próximos) foi comparada com o desempenho geral desse grupo:")
        
        for nome_materia, texto_comparacao in comparacoes:
            st.markdown(f"**{nome_materia}:** {texto_comparacao}")

# ===================================================================
# 5. EXECUÇÃO PRINCIPAL DO DASHBOARD (MERGE)
# ===================================================================
st.title('Dashboard de Análise e Previsão ENEM 2021 a 2023 - Ceará')

# Garante que a pasta de dados local existe
PASTA_DADOS.mkdir(exist_ok=True)

# Carrega os 4 artefatos (modelo, colunas, scaler, y_train)
modelo_knn, colunas_modelo, scaler_modelo, y_train_data = carregar_artefatos_modelo()

# Carrega os dados para a aba de análise
df_ceara = carregar_dados_ceara()

# Verifica se todos os arquivos essenciais foram carregados
if df_ceara is None or modelo_knn is None or scaler_modelo is None or y_train_data is None:
    st.error("Falha ao baixar ou carregar os arquivos necessários. Verifique os links e a sua conexão.")
    st.stop() 

# Cria as abas do dashboard
tab1, tab2 = st.tabs(["📊 Análise Exploratória", "🤖 Previsão de Notas"])

with tab1:
    aba_analise_exploratoria(df_ceara)
    
with tab2:
    # Passa os 4 artefatos para a função da aba de previsão
    aba_previsao_notas(modelo_knn, colunas_modelo, scaler_modelo, y_train_data)
