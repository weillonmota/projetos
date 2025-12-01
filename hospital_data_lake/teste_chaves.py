import os
from pathlib import Path
from dotenv import load_dotenv

# 1. Define o caminho exato onde o .env deveria estar
BASEDIR = Path(__file__).resolve().parent
dotenv_path = BASEDIR / '.env'

print("--- DIAGNÓSTICO DE VARIÁVEIS DE AMBIENTE ---")
print(f"📂 Diretório do script: {BASEDIR}")
print(f"📄 Caminho esperado do .env: {dotenv_path}")

# 2. Verifica se o arquivo existe fisicamente
if dotenv_path.exists():
    print("✅ O arquivo .env foi ENCONTRADO no disco.")
    
    # Tenta ler o conteúdo bruto (sem processar) para ver se tem algo escrito
    try:
        with open(dotenv_path, 'r') as f:
            conteudo = f.read()
            if "AWS_BUCKET_NAME" in conteudo:
                print("✅ A string 'AWS_BUCKET_NAME' existe dentro do arquivo.")
            else:
                print("❌ O arquivo existe, mas NÃO TEM a variável 'AWS_BUCKET_NAME' escrita nele.")
    except Exception as e:
        print(f"❌ Erro ao tentar abrir o arquivo: {e}")
else:
    print("❌ O arquivo .env NÃO FOI ENCONTRADO. Verifique se o nome não está como '.env.txt'.")

print("-" * 30)

# 3. Carrega as variáveis para o Python
load_dotenv(dotenv_path=dotenv_path)

# 4. Verifica o que o Python "enxerga"
bucket = os.getenv('AWS_BUCKET_NAME')
aws_key = os.getenv('AWS_ACCESS_KEY_ID')

if bucket:
    print(f"✅ BUCKET_NAME carregado: '{bucket}'")
else:
    print(f"❌ BUCKET_NAME está NULO (None).")

if aws_key:
    # Mostra só os 4 primeiros digitos para conferência segura
    print(f"✅ AWS_ACCESS_KEY_ID carregado: '{aws_key[:4]}...****'")
else:
    print(f"❌ AWS_ACCESS_KEY_ID está NULO (None).")

print("-" * 30)