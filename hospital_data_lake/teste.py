import pandas as pd
import boto3
import os
from io import BytesIO
from dotenv import load_dotenv
from pathlib import Path

# --- CONFIGURAÇÃO ---
BASEDIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASEDIR / '.env')

AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')

def auditar_gold():
    print("🕵️‍♂️ Auditando a Camada Gold (Direto do S3)...")
    
    if not BUCKET_NAME:
        print("❌ Erro: BUCKET_NAME não encontrado.")
        return

    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
    
    arquivo_alvo = 'gold/dim_calendario.parquet'
    
    try:
        print(f"📥 Baixando para memória: {arquivo_alvo}")
        obj = s3.get_object(Bucket=BUCKET_NAME, Key=arquivo_alvo)
        
        # Lê o conteúdo binário do S3
        conteudo_parquet = BytesIO(obj['Body'].read())
        
        # O Pandas lê esse conteúdo binário
        df = pd.read_parquet(conteudo_parquet)
        
        print("\n✅ Sucesso! Arquivo Parquet lido corretamente.")
        print("-" * 30)
        print(f"Total de linhas: {len(df)}")
        print("-" * 30)
        print("Amostra dos dados:")
        print(df.head())
        print("-" * 30)
        print("Tipos de dados (Schema):")
        print(df.dtypes)
        
    except Exception as e:
        print(f"❌ Erro ao ler o arquivo: {e}")
        print("Dica: Verifique se o script 'gold_star_schema.py' rodou com sucesso antes.")

if __name__ == "__main__":
    auditar_gold()