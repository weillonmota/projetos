import pandas as pd
import boto3
import os
from io import StringIO
from dotenv import load_dotenv
from pathlib import Path

# --- CARREGAMENTO DO .env ---
BASEDIR = Path(__file__).resolve().parent
dotenv_path = BASEDIR / '.env'
load_dotenv(dotenv_path=dotenv_path) 

# --- CONFIGURAÇÕES ---
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')

S3_BRONZE_PREFIX = 'bronze/'
S3_SILVER_KEY = 'silver/internacoes_unificadas.csv'

def etl_process_v3():
    print("🚀 [ETL V3] Iniciando: Leitura Híbrida + Limpeza + Ordenação...")
    
    if not BUCKET_NAME:
        print("❌ Erro: BUCKET_NAME não encontrado no .env")
        return

    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
    
    # 1. Listar arquivos
    try:
        response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=S3_BRONZE_PREFIX)
        arquivos = [obj['Key'] for obj in response.get('Contents', []) 
                    if obj['Key'].lower().endswith('.csv')
                    and 'comentarios' not in obj['Key'].lower()]
    except Exception as e:
        print(f"❌ Erro ao listar bucket: {e}")
        return

    print(f"📂 Encontrados {len(arquivos)} arquivos CSV.")
    
    lista_dfs = []

    # 2. Loop de Leitura e Limpeza (ARQUIVO POR ARQUIVO)
    for arquivo in arquivos:
        nome_arquivo = arquivo.split('/')[-1]
        try:
            obj = s3.get_object(Bucket=BUCKET_NAME, Key=arquivo)
            raw_data = obj['Body'].read()
            
            # --- CORREÇÃO DE ENCODING (INTELIGENTE) ---
            # Tenta UTF-8 primeiro (padrão web). Se falhar, usa Latin-1 (padrão legado).
            try:
                content = raw_data.decode('utf-8')
            except UnicodeDecodeError:
                content = raw_data.decode('latin1')
            
            # Tenta ler CSV
            try:
                df_temp = pd.read_csv(StringIO(content), sep=';')
                if len(df_temp.columns) < 2:
                    df_temp = pd.read_csv(StringIO(content), sep=',')
            except:
                 df_temp = pd.read_csv(StringIO(content), sep=',')

            # --- LIMPEZA DE DADOS (DENTRO DO LOOP) ---
            qtd_antes = len(df_temp)

            # 1. Remove linhas totalmente vazias
            df_temp.dropna(how='all', inplace=True)
            
            # 2. Limpeza Crítica: Se faltar Idade, Sexo ou Município, remove a linha
            # (Normaliza nomes para garantir que encontra as colunas mesmo se maiúscula/minúscula)
            col_map = {c: c.lower() for c in df_temp.columns}
            cols_criticas = []
            for original, lower in col_map.items():
                if 'idade' in lower or 'sexo' in lower or 'munic' in lower:
                    cols_criticas.append(original)
            
            if cols_criticas:
                df_temp.dropna(subset=cols_criticas, how='any', inplace=True)
            
            # 3. Filtra datas inválidas
            if 'data_internacao' in df_temp.columns:
                 df_temp = df_temp[df_temp['data_internacao'].notna()]

            qtd_depois = len(df_temp)
            removidas = qtd_antes - qtd_depois

            if qtd_depois > 0:
                print(f"   -> Lendo: {nome_arquivo}")
                if removidas > 0:
                    print(f"      🧹 Limpeza: {removidas} linhas incompletas removidas.")
                lista_dfs.append(df_temp)
            else:
                print(f"   ⚠️ ALERTA: Arquivo {nome_arquivo} ficou vazio após limpeza.")

        except Exception as e:
            print(f"   ❌ Erro em {nome_arquivo}: {e}")

    # 3. Consolidação Final
    if lista_dfs:
        df_final = pd.concat(lista_dfs, ignore_index=True)
        print(f"\n📊 Total Bruto: {len(df_final)} linhas.")

        # --- TRATAMENTO DE DATA E ORDENAÇÃO ---
        print("⏳ Convertendo e ordenando datas...")
        
        # Converte para datetime e remove erros
        df_final['data_internacao'] = pd.to_datetime(df_final['data_internacao'], dayfirst=True, errors='coerce')
        df_final = df_final.dropna(subset=['data_internacao'])
        
        # Ordena cronologicamente
        df_final.sort_values(by='data_internacao', ascending=True, inplace=True)
        
        print(f"✅ Ordenação concluída. Período: de {df_final['data_internacao'].min()} até {df_final['data_internacao'].max()}")

        # Salva no S3 (Silver)
        print("💾 Salvando na Silver...")
        csv_buffer = StringIO()
        # Salva como UTF-8-SIG (Universal para Excel) e separado por ponto e vírgula
        df_final.to_csv(csv_buffer, index=False, sep=';', encoding='utf-8-sig', date_format='%d/%m/%Y %H:%M')
        
        s3.put_object(Bucket=BUCKET_NAME, Key=S3_SILVER_KEY, Body=csv_buffer.getvalue())
        print(f"🏁 SUCESSO! Arquivo final salvo em: {S3_SILVER_KEY}")
    else:
        print("❌ Nenhum dado processado.")

if __name__ == "__main__":
    etl_process_v3()