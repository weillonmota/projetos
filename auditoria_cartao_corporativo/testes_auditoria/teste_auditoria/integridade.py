import os
import json
from datetime import datetime
import requests


def registrar_log_integridade(mensagem: str, status_code: int | None = None) -> None:
    """Grava o resultado do teste de integridade no arquivo de log corporativo."""
    data_hora: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status_info: str = f" [Status HTTP: {status_code}]" if status_code else ""
    linha_log: str = f"[{data_hora}]{status_info} {mensagem}\n"

    log_path = os.path.join(os.path.dirname(__file__), "../logs/auditoria_integridade.log")
    with open(log_path, mode="a", encoding="utf-8") as f:
        f.write(linha_log)


def testar_violacao_integridade() -> None:
    print("[TESTE 2] Iniciando teste de Integridade e Injeção de Dados...")
    registrar_log_integridade("--- INÍCIO DO TESTE DE INTEGRIDADE ---")

    # Endpoint de escrita simulado baseado na estrutura do Airtable
    url_alteracao: str = (
        "https://airtable.com/v0.3/application/appjku7kXHQcVCcXM/alter"
    )

    headers: dict[str, str] = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        ),
        "Content-Type": "application/json",
    }

    # Carga maliciosa: tentando injetar um registro falso de gasto concentrado
    dados_maliciosos: dict = {
        "msg": "inject",
        "row": {
            "ANO_MES": "2026-05",
            "NOME PORTADOR": "AUDITOR_INVASOR_TESTE",
            "NOME FAVORECIDO": "EMPRESA FANTASMA LTDA",
            "GASTO_FORNECEDOR_MES": 500000.00,
            "PERC_CONCENTRACAO": 100.0,
        },
    }

    try:
        # Envia uma requisição POST anônima tentando forçar a inserção do registro
        resposta = requests.post(
            url_alteracao, headers=headers, json=dados_maliciosos, timeout=10
        )

        # Se o Airtable aceitar a gravação sem chave de API/Token
        if resposta.status_code in [200, 201]:
            msg_falha: str = (
                "❌ CRÍTICO - FALHA DE INTEGRIDADE: O sistema aceitou a injeção"
                " de dados anônima! A base de dados do dashboard foi violada."
            )
            print(msg_falha)
            registrar_log_integridade(msg_falha, resposta.status_code)

        # Se o Airtable recusar por falta de privilégios (Cenário correto de segurança)
        elif resposta.status_code in [401, 403, 404, 422]:
            msg_sucesso: str = (
                "✅ SUCESSO: O sistema bloqueou a tentativa de alteração"
                " anônima. Os dados originais do Airtable permanecem íntegros."
            )
            print(msg_sucesso)
            registrar_log_integridade(msg_sucesso, resposta.status_code)
        else:
            msg_indeterminado: str = (
                "⚠️ ALERTA: Resposta inesperada do servidor durante a tentativa"
                " de escrita."
            )
            print(msg_indeterminado)
            registrar_log_integridade(msg_indeterminado, resposta.status_code)

    except requests.exceptions.RequestException as e:
        msg_erro: str = f"❌ ERRO EXCEÇÃO DE CONEXÃO: {e}"
        print(msg_erro)
        registrar_log_integridade(msg_erro)

    registrar_log_integridade("--- FIM DO TESTE DE INTEGRIDADE ---\n")
    print("[INFO] Processo finalizado. Verifique o arquivo 'auditoria_integridade.log'.")


if __name__ == "__main__":
    testar_violacao_integridade()