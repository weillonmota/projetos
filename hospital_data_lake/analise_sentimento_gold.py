import pandas as pd
import boto3
import os
from io import StringIO
from dotenv import load_dotenv
from pathlib import Path
from pysentimiento import create_analyzer

# --- CONFIGURAÇÃO ---
BASEDIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASEDIR / '.env')

AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')

S3_INPUT_KEY = 'silver/comentarios_tratados.csv'
S3_OUTPUT_KEY = 'gold/comentarios_sentimento_bert.csv'

def processar_com_bert():
    print("🚀 [GOLD] Iniciando Análise com BERT (Pysentimiento)...")
    
    # 1. Carrega o Modelo (Isso baixa ~500MB na primeira vez)
    print("🧠 Carregando modelo 'bertweet-pt-sentiment'...")
    analyzer = create_analyzer(task="sentiment", lang="pt")

    # 2. Conecta no S3
    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
    print("📥 Baixando dados da Silver...")
    obj = s3.get_object(Bucket=BUCKET_NAME, Key=S3_INPUT_KEY)
    df = pd.read_csv(obj['Body'], sep=';', encoding='utf-8')

    # 3. Processamento
    print("⚙️ Analisando sentimentos (Isso é mais lento que o VADER, mas mais preciso)...")
    
    sentimentos = []
    scores = []
    
    total = len(df)
    for i, row in df.iterrows():
        texto = row['texto_limpo']
        
        # O modelo processa direto o texto em PT com emojis
        resultado = analyzer.predict(texto)
        
        # O resultado vem como "POS", "NEG", "NEU"
        # Mapeamos para o seu padrão
        mapa = {'POS': 'Positivo', 'NEG': 'Negativo', 'NEU': 'Neutro'}
        sentimentos.append(mapa[resultado.output])
        
        # Pegamos a probabilidade da classe escolhida como "Score"
        # O modelo retorna um dicionário de probabilidades {POS: 0.98, NEG: 0.01...}
        probabilidade = resultado.probas[resultado.output]
        
        # Ajuste de sinal para manter seu padrão (-1 a 1) visual
        if resultado.output == 'NEG':
            scores.append(probabilidade * -1)
        elif resultado.output == 'NEU':
            scores.append(0.0)
        else:
            scores.append(probabilidade)

        if i % 50 == 0:
            print(f"   ... Processado {i}/{total}")

    df['sentimento'] = sentimentos
    df['score_sentimento'] = scores
    
    # 4. Resultados
    print("\n--- Amostra Final (BERT) ---")
    print(df[['texto_limpo', 'sentimento', 'score_sentimento']].head(10))
    
    print("\n📊 Resumo:")
    print(df['sentimento'].value_counts())

    # 5. Salvar
    print(f"\n💾 Salvando em: {S3_OUTPUT_KEY}")
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False, sep=';', encoding='utf-8-sig')
    s3.put_object(Bucket=BUCKET_NAME, Key=S3_OUTPUT_KEY, Body=csv_buffer.getvalue())
    print("🏁 Sucesso!")

if __name__ == "__main__":
    processar_com_bert()