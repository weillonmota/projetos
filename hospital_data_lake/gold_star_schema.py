import duckdb
import boto3
import os
import pandas as pd
from io import BytesIO
from dotenv import load_dotenv
from pathlib import Path

# --- CONFIGURAÇÃO ---
BASEDIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASEDIR / '.env')

AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')

S3_SILVER_KEY = 'silver/internacoes_unificadas.csv'
S3_GOLD_PREFIX = 'gold/'

def processar_gold_star_schema():
    print("🚀 [GOLD] Iniciando modelagem Dimensional (Star Schema)...")
    
    if not BUCKET_NAME:
        print("❌ Erro: BUCKET_NAME não encontrado.")
        return
    
    # 1. Baixar o CSV da Silver
    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
    
    try:
        print("📥 Baixando dados da Silver (Tabelão)...")
        obj = s3.get_object(Bucket=BUCKET_NAME, Key=S3_SILVER_KEY)
        # Lê com Pandas
        df_silver = pd.read_csv(obj['Body'], sep=';', encoding='utf-8')
        
        # --- CORREÇÃO DO ERRO AQUI ---
        # Renomeia 'município' para 'municipio' para facilitar o SQL
        df_silver.rename(columns={'município': 'municipio'}, inplace=True)
        
        # Garante que a data seja data mesmo
        df_silver['data_internacao'] = pd.to_datetime(df_silver['data_internacao'], dayfirst=True)
        
    except Exception as e:
        print(f"❌ Erro ao ler a Silver: {e}")
        return
    
    # 2. Iniciar DuckDB
    print("🦆 Iniciando motor SQL (DuckDB)...")
    con = duckdb.connect(database=':memory:')
    con.register('tb_silver', df_silver)
    
    # ---------------------------------------------------------
    # 3. CRIAR DIMENSÕES (SQL)
    # ---------------------------------------------------------
    
    print("🔨 [1/4] Criando Dimensão: Especialidade...")
    con.execute("""
        CREATE TABLE dim_especialidade AS
        SELECT 
            row_number() OVER (ORDER BY especialidade) AS id_especialidade,
            especialidade AS nome_especialidade
        FROM (SELECT DISTINCT especialidade FROM tb_silver WHERE especialidade IS NOT NULL)
    """)
    
    print("🔨 [2/4] Criando Dimensão: Município...")
    # Agora usamos 'municipio' sem acento, pois renomeamos no Pandas acima
    con.execute("""
        CREATE TABLE dim_municipio AS
        SELECT 
            row_number() OVER (ORDER BY municipio) AS id_municipio,
            municipio AS nome_municipio
        FROM (SELECT DISTINCT municipio FROM tb_silver WHERE municipio IS NOT NULL)
    """)
    
    print("🔨 [3/4] Criando Dimensão: Calendário...")
    con.execute("""
        CREATE TABLE dim_calendario AS
        SELECT DISTINCT
            data_internacao AS id_calendario,
            YEAR(data_internacao) AS ano,
            MONTH(data_internacao) AS mes,
            DAY(data_internacao) AS dia,
            CASE 
                WHEN MONTH(data_internacao) <= 6 THEN 1 
                ELSE 2 
            END AS semestre
        FROM tb_silver
        WHERE data_internacao IS NOT NULL
        ORDER BY 1
    """)

    # ---------------------------------------------------------
    # 4. CRIAR FATO
    # ---------------------------------------------------------
    print("🔨 [4/4] Criando Tabela Fato: Internações...")
    con.execute("""
        CREATE TABLE fato_internacoes AS
        SELECT 
            s.data_internacao AS id_calendario,
            m.id_municipio,
            e.id_especialidade,
            s.idade,
            s.sexo,
            1 AS qtd_internacao
        FROM tb_silver s
        LEFT JOIN dim_municipio m ON s.municipio = m.nome_municipio
        LEFT JOIN dim_especialidade e ON s.especialidade = e.nome_especialidade
    """)
    
    # ---------------------------------------------------------
    # 5. SALVAR NO S3
    # ---------------------------------------------------------
    print("💾 Salvando tabelas na camada Gold (Parquet)...")
    
    tabelas = ['dim_especialidade', 'dim_municipio', 'dim_calendario', 'fato_internacoes']
    
    for tabela in tabelas:
        df_export = con.table(tabela).df()
        
        parquet_buffer = BytesIO()
        df_export.to_parquet(parquet_buffer, index=False)
        
        key = f"{S3_GOLD_PREFIX}{tabela}.parquet"
        s3.put_object(Bucket=BUCKET_NAME, Key=key, Body=parquet_buffer.getvalue())
        print(f"   ✅ {tabela} salva em: {key}")

    print("🏁 Sucesso! Data Warehouse criado.")

if __name__ == "__main__":
    processar_gold_star_schema()