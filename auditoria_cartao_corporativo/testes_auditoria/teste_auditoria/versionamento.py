import os
import json
from datetime import datetime
import requests


def registrar_log_governance(mensagem: str) -> None:
    """Grava o resultado da auditoria de versionamento no arquivo de log."""
    data_hora: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linha_log: str = f"[{data_hora}] {mensagem}\n"

    log_path = os.path.join(os.path.dirname(__file__), "../logs/auditoria_governança.log")
    with open(log_path, mode="a", encoding="utf-8") as f:
        f.write(linha_log)


def testar_rastreabilidade_airtable() -> None:
    print("[TESTE 3] Iniciando teste de Rastreabilidade e Versionamento...")
    registrar_log_governance("--- INÍCIO DO TESTE DE GOVERNANÇA E VERSIONAMENTO ---")

    # URL pública da sua aplicação
    url_aplicacao: str = (
        "https://airtable.com/appjku7kXHQcVCcXM/pagi1gIG0RYr1R3HO"
    )

    try:
        resposta = requests.get(url_aplicacao, timeout=10)

        if resposta.status_code == 200:
            print("Analisando metadados da aplicação em busca de trilhas de auditoria...")
            
            # Verificamos se o HTML ou a estrutura expõe alguma variável de histórico corporativo (Enterprise Audit Log)
            # Geralmente, views públicas ocultam completamente os logs de quem alterou os dados por segurança.
            if "audit" in resposta.text.lower() or "history" in resposta.text.lower():
                msg_sucesso: str = (
                    "✅ SUCESSO: Foram encontrados indícios de logs de auditoria"
                    " ou histórico de revisões integrados na aplicação."
                )
                print(msg_sucesso)
                registrar_log_governance(msg_sucesso)
            else:
                msg_falha: str = (
                    "❌ OBSERVAÇÃO / RISCO DE GOVERNANÇA: A visualização pública"
                    " não expõe logs de auditoria (Audit Trail). Não é possível"
                    " rastrear quem alterou as regras ou os dados através desta interface."
                )
                print(msg_falha)
                registrar_log_governance(msg_falha)
        else:
            print(f"Erro ao acessar aplicação. Status: {resposta.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")

    registrar_log_governance("--- FIM DO TESTE DE GOVERNANÇA ---\n")
    print("[INFO] Processo finalizado. Verifique 'auditoria_governança.log'.")


if __name__ == "__main__":
    testar_rastreabilidade_airtable()