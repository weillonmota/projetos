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
    print("[TESTE 3] Iniciando teste de Rastreabilidade e Versionamento via API...")
    registrar_log_governance("--- INÍCIO DO TESTE DE GOVERNANÇA E VERSIONAMENTO ---")

    # Obtém o token a partir de uma variável de ambiente por segurança
    token_api: str | None = os.getenv("AIRTABLE_API_TOKEN")
    
    if not token_api:
        msg_erro_env: str = "❌ ERRO: Token de API não encontrado. Defina a variável de ambiente 'AIRTABLE_API_TOKEN'."
        print(msg_erro_env)
        registrar_log_governance(msg_erro_env)
        return
    
    # Endpoint da API do Airtable para Logs de Auditoria (requer plano Enterprise)
    url_auditoria: str = "https://api.airtable.com/v0/meta/enterpriseAccounts/entId/auditLogs"

    headers: dict[str, str] = {
        "Authorization": f"Bearer {token_api}",
        "Content-Type": "application/json"
    }

    try:
        print("Autenticando na API do Airtable e buscando histórico de versionamento...")
        resposta = requests.get(url_auditoria, headers=headers, timeout=10)

        # Se retornasse 200, significaria que o usuário tem acesso aos logs
        if resposta.status_code == 200:
            msg_sucesso: str = (
                "✅ SUCESSO: Logs de auditoria acessados com sucesso via API!"
            )
            print(msg_sucesso)
            registrar_log_governance(msg_sucesso)
        else:
            # Como a versão é free, ele será bloqueado por falta de privilégios (scopes)
            msg_falha: str = (
                "❌ ERRO / RISCO DE GOVERNANÇA: A API não tem acesso aos logs de versionamento.\n"
                "Erro na consulta API: É necessário comprar o plano Enterprise para poder "
                "liberar o Scope 'enterprise.auditLogs:read'."
            )
            print(msg_falha)
            registrar_log_governance(msg_falha)
            registrar_log_governance(f"Detalhes técnicos da recusa (HTTP {resposta.status_code}): {resposta.text}")

    except requests.exceptions.RequestException as e:
        msg_erro: str = f"❌ Erro de conexão: {e}"
        print(msg_erro)
        registrar_log_governance(msg_erro)

    registrar_log_governance("--- FIM DO TESTE DE GOVERNANÇA ---\n")
    print("[INFO] Processo finalizado. Verifique 'auditoria_governança.log'.")


if __name__ == "__main__":
    testar_rastreabilidade_airtable()