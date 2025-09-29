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
import requests
from pathlib import Path

st.set_page_config(layout="wide", page_title="Dashboard ENEM - Ceará")

# ===================================================================
# 2. CONSTANTES, URLs E CAMINHOS LOCAIS
# ===================================================================
# URLs dos seus arquivos no GitHub Releases
MODELO_URL = "https://github.com/weillonmota/projetos/releases/download/v1.0-dados/modelo_knn.joblib"
COLUNAS_URL = "https://github.com/weillonmota/projetos/releases/download/v1.0-dados/colunas_modelo.json"
DADOS_URL = "https://github.com/weillonmota/projetos/releases/download/v1.0-dados/dados_ceara.csv"

# Caminhos locais onde os arquivos serão salvos no ambiente do Streamlit
PASTA_DADOS = Path("dados_app")
CAMINHO_MODELO = PASTA_DADOS / "modelo_knn.joblib"
CAMINHO_COLUNAS = PASTA_DADOS / "colunas_modelo.json"
CAMINHO_DADOS = PASTA_DADOS / "dados_ceara.csv"

# Dicionários de mapeamento (inalterados do seu código original)
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
# 3. FUNÇÕES DE DOWNLOAD E CARREGAMENTO
# ===================================================================
def baixar_arquivo(url: str, destino: Path):
    """Baixa um arquivo de uma URL para um destino local se ele não existir."""
    if not destino.exists():
        with st.spinner(f"Baixando {destino.name}... Isso pode levar alguns segundos."):
            try:
                response = requests.get(url, stream=True)
                response.raise_for_status()
                destino.parent.mkdir(parents=True, exist_ok=True)
                with open(destino, "wb") as f:
                    for chunk in response
