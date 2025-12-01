import pandas as pd
import numpy as np
import os
from typing import List

def processar_dados_enem(caminho_arquivo: str, tamanho_amostra: int = 10000) -> None:
    # 1. Definição das colunas
    colunas_leitura: List[str] = [
        'NU_INSCRICAO', 
        'NU_NOTA_MT', 'NU_NOTA_CN', 'NU_NOTA_LC', 'NU_NOTA_CH', 'NU_NOTA_REDACAO',
        'Q006', 'Q002', 'TP_ESCOLA', 'TP_COR_RACA',
        'SG_UF_PROVA'  # Usada como proxy para residência
    ]

    print(f"Iniciando leitura do arquivo: {caminho_arquivo}")
    print("Aguarde...")
    
    try:
        # Lê o arquivo original (que usa ; e latin1)
        df = pd.read_csv(caminho_arquivo, sep=';', encoding='latin1', usecols=colunas_leitura)
    except ValueError as e:
        print(f"ERRO NA LEITURA: {e}")
        return

    # Renomear para o padrão do projeto
    df.rename(columns={'SG_UF_PROVA': 'SG_UF_RESIDENCIA'}, inplace=True)
    
    print(f"Registros brutos carregados: {len(df)}")

    # 2. Limpeza (Remover quem não tem nota)
    colunas_notas = ['NU_NOTA_MT', 'NU_NOTA_CN', 'NU_NOTA_LC', 'NU_NOTA_CH', 'NU_NOTA_REDACAO']
    df_limpo = df.dropna(subset=colunas_notas).copy()
    print(f"Registros válidos (com notas): {len(df_limpo)}")

    # 3. Amostragem Aleatória
    if len(df_limpo) > tamanho_amostra:
        df_final = df_limpo.sample(n=tamanho_amostra, random_state=42)
        print(f"Amostra de {tamanho_amostra} selecionada.")
    else:
        df_final = df_limpo

    df_final.reset_index(drop=True, inplace=True)
    
    # 4. Salvar com separador PONTO E VÍRGULA (Mudança solicitada)
    diretorio_atual = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(diretorio_atual, 'dados_enem_processados.csv')
    
    # Adicionamos sep=';' aqui
    df_final.to_csv(output_file, index=False, sep=';')
    
    print(f"Sucesso! Arquivo gerado em: {output_file}")
    

if __name__ == "__main__":
    diretorio_script = os.path.dirname(os.path.abspath(__file__))
    
    # Caminho ajustado
    caminho_csv = os.path.join(
        diretorio_script, 
        '..', 
        'dados_brutos', 
        'MICRODADOS_ENEM_2023.csv'
    )
    caminho_csv = os.path.normpath(caminho_csv)

    if os.path.exists(caminho_csv):
        processar_dados_enem(caminho_csv)
    else:
        print(f"ERRO: Arquivo não encontrado em {caminho_csv}")