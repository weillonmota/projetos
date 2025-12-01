import pandas as pd
import boto3
import os
import re
from io import StringIO
from dotenv import load_dotenv
from pathlib import Path

# --- CONFIGURAÇÃO ---
BASEDIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASEDIR / '.env')

AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')

S3_INPUT_KEY = 'bronze/comentarios_huol_completo_223posts.csv'
S3_OUTPUT_KEY = 'silver/comentarios_tratados.csv'

# --- FUNÇÕES DE LIMPEZA ---

def limpar_texto_manter_emoji(texto):
    """
    Limpa formatação e links, mas MANTÉM os emojis originais (😢).
    """
    if not isinstance(texto, str):
        return ""
    
    # NÃO fazemos demojize. Mantemos o emoji visual.
    
    # Remove URLs
    texto_sem_link = re.sub(r'http\S+', '', texto)
    
    # Remove quebras de linha e espaços duplos
    return re.sub(r'\s+', ' ', texto_sem_link).strip()

def extrair_numero_curtidas(valor):
    """Extrai apenas o número inteiro."""
    numeros = re.findall(r'\d+', str(valor))
    return int(numeros[0]) if numeros else 0

def filtrar_lixo_scraping(df):
    """
    Remove artefatos de coleta (botões, contadores e datas soltas no texto).
    """
    qtd_inicial = len(df)
    
    # 1. Blacklist de Interface
    lixo_interface = [
        'Seguir', 'Responder', 'Ver tradução', 
        'Ocultar', 'Ver todas as respostas', 'Ver respostas'
    ]
    df = df[~df['texto_limpo'].isin(lixo_interface)]
    df = df[~df['texto_limpo'].str.contains('Ver todas as', case=False)]
    
    # 2. Lixo Numérico
    df = df[~df['texto_limpo'].str.match(r'^\d+$')]
    
    # 3. Lixo de Datas soltas (O filtro "Porteiro")
    # Pega linhas que são APENAS datas (ex: "27 de novembro de 2024")
    padrao_data = r'^[\d\s]*\d{1,2}\s+de\s+[a-zA-Zç]+(\s+de\s+\d{4})?.*$'
    
    mask_eh_data = df['texto_limpo'].str.match(padrao_data, case=False)
    mask_eh_curto = df['texto_limpo'].str.len() < 40 # Só deleta se for curto (sem contexto)
    
    df = df[~(mask_eh_data & mask_eh_curto)]
    
    removidos = qtd_inicial - len(df)
    if removidos > 0:
        print(f"      🧹 Faxina de Scraping: {removidos} linhas removidas.")
    
    return df

def etl_comentarios():
    print("🚀 [ETL Comentários V5] Iniciando (Emojis Nativos + Filtro Data)...")
    
    if not BUCKET_NAME:
        print("❌ Erro: BUCKET_NAME não encontrado.")
        return

    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
    
    try:
        print(f"📥 Baixando Bronze: {S3_INPUT_KEY}")
        obj = s3.get_object(Bucket=BUCKET_NAME, Key=S3_INPUT_KEY)
        # utf-8 garante que o emoji 😢 seja lido corretamente
        df = pd.read_csv(obj['Body'], encoding='utf-8')
    except Exception as e:
        print(f"❌ Erro ao ler arquivo: {e}")
        return

    print("⚙️ Aplicando regras de limpeza...")
    
    # A. Limpeza de Texto (Mantendo Emoji)
    df['texto_limpo'] = df['Texto'].apply(limpar_texto_manter_emoji)
    
    # B. Filtro de Lixo de Scraping (Datas no texto, botões)
    df = filtrar_lixo_scraping(df)
    
    # C. Dedup
    df.drop_duplicates(subset=['texto_limpo', 'Autor'], inplace=True)
    
    # D. Tratamento de Data e REMOÇÃO DE VAZIOS
    # errors='coerce' transforma lixo em NaT (Not a Time)
    df['data_publicacao'] = pd.to_datetime(df['Data'], errors='coerce').dt.date
    
    # [NOVO] Se a data for nula (NaT), joga a linha fora
    qtd_antes_data = len(df)
    df.dropna(subset=['data_publicacao'], inplace=True)
    removidos_data = qtd_antes_data - len(df)
    if removidos_data > 0:
         print(f"      📅 Data Vazia: {removidos_data} linhas sem data removidas.")
    
    # E. Métricas
    df['qtd_curtidas'] = df['Curtidas'].apply(extrair_numero_curtidas)
    
    # F. Seleção Final
    df_final = df[['data_publicacao', 'texto_limpo', 'qtd_curtidas', 'ID Post']]
    df_final = df_final[df_final['texto_limpo'] != '']
    
    print(f"📊 Total Final Limpo: {len(df_final)} linhas.")
    
    # Validação na tela
    print("\n--- Amostra (Verifique os Emojis) ---")
    print(df_final[['texto_limpo']].head(5))

    print(f"\n💾 Salvando Silver: {S3_OUTPUT_KEY}")
    csv_buffer = StringIO()
    # UTF-8-SIG é OBRIGATÓRIO para o Excel ver o emoji 😢
    df_final.to_csv(csv_buffer, index=False, sep=';', encoding='utf-8-sig')
    
    s3.put_object(Bucket=BUCKET_NAME, Key=S3_OUTPUT_KEY, Body=csv_buffer.getvalue())
    print("🏁 Sucesso!")

if __name__ == "__main__":
    etl_comentarios()