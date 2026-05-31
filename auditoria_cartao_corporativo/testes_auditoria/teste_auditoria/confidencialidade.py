import os
import json
from datetime import datetime
import requests


def registrar_log(mensagem: str, dados_brutos: dict | None = None) -> None:
    """Grava o resultado do teste e o dump dos dados extraídos no arquivo de log."""
    data_hora: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linha_log: str = f"[{data_hora}] {mensagem}\n"

    log_path = os.path.join(os.path.dirname(__file__), "../logs/auditoria_confidencialidade.log")
    with open(log_path, mode="a", encoding="utf-8") as f:
        f.write(linha_log)
        if dados_brutos:
            f.write("[DADOS BRUTOS EXTRAÍDOS VIA API INTERNA]:\n")
            f.write(json.dumps(dados_brutos, indent=4, ensure_ascii=False))
            f.write("\n")


def testar_extracao_bruta_airtable() -> None:
    print("[TESTE 1 - EXTRAÇÃO BRUTA] Acessando API interna do painel...")
    registrar_log("--- INÍCIO DO TESTE DE EXTRAÇÃO BRUTA DE DADOS ---")

    # URL interna de dados correspondente à aplicação pública informada
    url_api_interna: str = (
        "https://airtable.com/v0.3/application/appjku7kXHQcVCcXM/read"
    )

    headers: dict[str, str] = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
    }

    # Parâmetros que o Airtable exige para identificar a página de visualização pública
    params: dict[str, str] = {
        "stringifiedObjectIdsToRead": '["pagi1gIG0RYr1R3HO"]',
    }

    try:
        resposta = requests.get(
            url_api_interna, headers=headers, params=params, timeout=15
        )

        if resposta.status_code == 200:
            dados_json: dict = resposta.json()

            # Verifica se a resposta contém a estrutura de dados esperada
            if "data" in dados_json or "dataByObjectId" in dados_json:
                msg_sucesso: str = (
                    "❌ CRÍTICO - FALHA GRAVE DE CONFIDENCIALIDADE: O endpoint da"
                    " API interna está totalmente exposto de forma pública."
                    " Os dados estruturados foram capturados integralmente sem"
                    " autenticação."
                )
                print(msg_sucesso)
                print(
                    "[INFO] Dados obtidos com sucesso. Gravando cópia integral"
                    " no log..."
                )

                # Salva o JSON completo com todas as linhas, colunas e valores originais
                registrar_log(msg_sucesso, dados_brutos=dados_json)
            else:
                msg_estrutura_mudou: str = (
                    "⚠️ ALERTA: A requisição retornou sucesso (200), mas a"
                    " estrutura do JSON difere do esperado. Verifique o log."
                )
                print(msg_estrutura_mudou)
                registrar_log(msg_estrutura_mudou, dados_brutos=dados_json)

        else:
            msg_bloqueio: str = (
                "✅ SUCESSO: O Airtable barrou a requisição direta à API"
                f" interna. Status HTTP: {resposta.status_code}"
            )
            print(msg_bloqueio)
            registrar_log(msg_bloqueio)

    except requests.exceptions.RequestException as e:
        msg_erro: str = f"❌ ERRO EXCEÇÃO DE CONEXÃO: {e}"
        print(msg_erro)
        registrar_log(msg_erro)

    registrar_log("--- FIM DO TESTE DE EXTRAÇÃO BRUTA DE DADOS ---\n")
    print("[INFO] Processo finalizado. Verifique o arquivo 'auditoria_confidencialidade.log'.")


if __name__ == "__main__":
    testar_extracao_bruta_airtable()