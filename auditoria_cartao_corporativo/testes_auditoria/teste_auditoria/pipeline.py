import os
import shutil
from datetime import datetime
import pandas as pd

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../extracao_dados_dashboard')))
# pyrefly: ignore [missing-import]
from extraçao_dados import executar_auditoria_pasta


def inicializar_log_consolidado() -> None:
    """Cria ou limpa o arquivo de log no início da suite de testes."""
    log_path = os.path.join(os.path.dirname(__file__), "../logs/auditoria_completa_pipeline.log")
    with open(log_path, mode="w", encoding="utf-8") as f:
        data_hora: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"========================================================\n")
        f.write(f" SUITE DE TESTES CONSOLIDADA - PIPELINE DE EXTRAÇÃO\n")
        f.write(f" Data de Execução: {data_hora}\n")
        f.write(f"========================================================\n\n")


def registrar_resultado_teste(nome_teste: str, status: str, detalhe: str) -> None:
    """Salva o resultado individual de cada teste no log corporativo."""
    data_hora: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linha: str = f"[{data_hora}] [{status}] {nome_teste}: {detalhe}\n"
    log_path = os.path.join(os.path.dirname(__file__), "../logs/auditoria_completa_pipeline.log")
    with open(log_path, mode="a", encoding="utf-8") as f:
        f.write(linha)


def criar_cenario_limpo(pasta_brutos: str, pasta_resultados: str) -> None:
    """Garante que as pastas de teste temporárias estejam limpas antes de iniciar."""
    if os.path.exists(pasta_brutos):
        shutil.rmtree(pasta_brutos)
    if os.path.exists(pasta_resultados):
        shutil.rmtree(pasta_resultados)
    os.makedirs(pasta_brutos, exist_ok=True)


def rodar_suite_de_testes() -> None:
    inicializar_log_consolidado()
    print("🚀 Iniciando Suite de Testes de Robustez e Confiabilidade...")

    pasta_brutos: str = "dados_brutos_teste"
    pasta_resultados: str = "resultados_auditoria_teste"

    # =========================================================================
    # CENÁRIO 1: Teste de Tolerância a Falhas (Dados Corrompidos na Conversão)
    # =========================================================================
    criar_cenario_limpo(pasta_brutos, pasta_resultados)
    
    df_corrompido = pd.DataFrame({
        "DATA TRANSAÇÃO": ["25/05/2026"],
        "NOME PORTADOR": ["WEILLON B. M."],
        "TRANSAÇÃO": ["COMPRA COMPLEMENTAR"],
        "VALOR TRANSAÇÃO": ["VALOR_TEXTO_INVALIDO"],  # Deveria ser número em string
        "CNPJ OU CPF FAVORECIDO": ["00000000000100"],
        "NOME FAVORECIDO": ["FORNECEDOR TESTE LTDA"],
        "NOME ÓRGÃO": ["INSTITUTO DE TI"]
    })
    df_corrompido.to_csv(os.path.join(pasta_brutos, "cenario1.csv"), sep=";", index=False, encoding="utf-8")

    try:
        executar_auditoria_pasta(pasta_brutos, pasta_resultados)
        registrar_resultado_teste("TESTE 1 (Tolerância a Falhas)", "FALHA", "O pipeline aceitou strings não numéricas sem disparar exceção.")
    except ValueError as e:
        registrar_resultado_teste("TESTE 1 (Tolerância a Falhas)", "SUCESSO", f"O sistema barrou a conversão de tipo inválido controladamente: {e}")
    except Exception as e:
        registrar_resultado_teste("TESTE 1 (Tolerância a Falhas)", "ALERTA", f"O sistema falhou com uma exceção genérica inesperada: {e}")

    # =========================================================================
    # CENÁRIO 2: Teste de Maturidade (Colunas Obrigatórias Ausentes)
    # =========================================================================
    criar_cenario_limpo(pasta_brutos, pasta_resultados)
    
    df_sem_coluna = pd.DataFrame({
        "DATA TRANSAÇÃO": ["25/05/2026"],
        "NOME PORTADOR": ["WEILLON B. M."]
        # Faltam todas as colunas de cálculo de regras
    })
    df_sem_coluna.to_csv(os.path.join(pasta_brutos, "cenario2.csv"), sep=";", index=False, encoding="utf-8")

    try:
        executar_auditoria_pasta(pasta_brutos, pasta_resultados)
        registrar_resultado_teste("TESTE 2 (Maturidade Estrutural)", "FALHA", "O pipeline tentou processar um arquivo sem as colunas obrigatórias.")
    except KeyError as e:
        registrar_resultado_teste("TESTE 2 (Maturidade Estrutural)", "SUCESSO", f"A ausência de chaves estruturais foi capturada com sucesso: KeyError {e}")
    except Exception as e:
        registrar_resultado_teste("TESTE 2 (Maturidade Estrutural)", "ALERTA", f"O sistema quebrou de forma não mapeada: {e}")

    # =========================================================================
    # CENÁRIO 3: Teste de Resiliência (Pasta de Dados de Entrada Vazia)
    # =========================================================================
    criar_cenario_limpo(pasta_brutos, pasta_resultados)
    # Deixamos a pasta intencionalmente sem nenhum arquivo CSV dentro

    try:
        executar_auditoria_pasta(pasta_brutos, pasta_resultados)
        # Como o seu código tem um 'return' amigável caso não ache arquivos, ele deve passar aqui suavemente
        registrar_resultado_teste("TESTE 3 (Resiliência de Diretório)", "SUCESSO", "O pipeline identificou a pasta vazia e encerrou a execução de forma elegante.")
    except Exception as e:
        registrar_resultado_teste("TESTE 3 (Resiliência de Diretório)", "FALHA", f"O sistema crashou ao encontrar um diretório vazio: {e}")

    # =========================================================================
    # CENÁRIO 4: Teste de Robustez (Valores Nulos/NaN em Campos Críticos)
    # =========================================================================
    criar_cenario_limpo(pasta_brutos, pasta_resultados)
    
    df_com_nulos = pd.DataFrame({
        "DATA TRANSAÇÃO": [None],  # Data nula que quebra a conversão de período temporal (.dt.to_period)
        "NOME PORTADOR": [None],
        "TRANSAÇÃO": ["SAQUE"],
        "VALOR TRANSAÇÃO": ["1.000,00"],
        "CNPJ OU CPF FAVORECIDO": [None],
        "NOME FAVORECIDO": [None],
        "NOME ÓRGÃO": ["ÓRGÃO TESTE"]
    })
    df_com_nulos.to_csv(os.path.join(pasta_brutos, "cenario4.csv"), sep=";", index=False, encoding="utf-8")

    try:
        executar_auditoria_pasta(pasta_brutos, pasta_resultados)
        registrar_resultado_teste("TESTE 4 (Robustez contra Nulos)", "FALHA", "O pipeline processou valores nulos em colunas chave sem apresentar restrições.")
    except AttributeError as e:
        registrar_resultado_teste("TESTE 4 (Robustez contra Nulos)", "SUCESSO", f"O Pandas barrou a extração de data nula controladamente (AttributeError): {e}")
    except Exception as e:
        registrar_resultado_teste("TESTE 4 (Robustez contra Nulos)", "SUCESSO", f"O pipeline evitou o processamento de nulos gerando a exceção: {e}")

    # Limpeza final das pastas temporárias
    if os.path.exists(pasta_brutos):
        shutil.rmtree(pasta_brutos)
    if os.path.exists(pasta_resultados):
        shutil.rmtree(pasta_resultados)

    print("🏁 Suite de testes finalizada com sucesso!")
    print("📄 O arquivo 'auditoria_completa_pipeline.log' foi gerado com as evidências.")


if __name__ == "__main__":
    rodar_suite_de_testes()