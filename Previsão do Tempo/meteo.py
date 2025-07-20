import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date, timedelta

# Cidades com coordenadas
cidades = {
    "São Paulo": {"lat": -23.55, "lon": -46.63},
    "Rio de Janeiro": {"lat": -22.91, "lon": -43.17},
    "Fortaleza": {"lat": -3.71, "lon": -38.54},
    "Belo Horizonte": {"lat": -19.92, "lon": -43.94}
}

# Datas
hoje = date.today()
data_inicio = hoje
data_fim = hoje + timedelta(days=6)

# Função para buscar previsão
def buscar_previsao(cidade, lat, lon):
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&daily=temperature_2m_max"
        f"&start_date={data_inicio}&end_date={data_fim}"
        f"&timezone=America/Sao_Paulo"
    )

    response = requests.get(url)
    if response.status_code == 200:
        dados = response.json()
        return pd.DataFrame({
            "data": dados["daily"]["time"],
            cidade: dados["daily"]["temperature_2m_max"]
        })
    else:
        print(f"[ERRO] Falha para {cidade}")
        return None

# Coleta para todas as cidades
dfs = []
for cidade, coord in cidades.items():
    df = buscar_previsao(cidade, coord["lat"], coord["lon"])
    if df is not None:
        dfs.append(df)

# Junta todas em um único DataFrame
df_merged = dfs[0]
for df in dfs[1:]:
    df_merged = pd.merge(df_merged, df, on="data")

df_merged["data"] = pd.to_datetime(df_merged["data"])

def mostrar_tabela(df):
    df_formatado = df.copy()
    for cidade in cidades:
        df_formatado[cidade] = df_formatado[cidade].map(lambda x: f"{x:.1f} °C")
    print("\n📋 Tabela de Previsão de Temperatura Máxima:\n")
    print(df_formatado.to_string(index=False))

mostrar_tabela(df_merged)

# Plot
plt.figure(figsize=(10, 6))
for cidade in cidades.keys():
    plt.plot(df_merged["data"], df_merged[cidade], label=cidade, marker="o")

plt.title("Previsão da Temperatura Máxima - Próximos 7 dias")
plt.xlabel("Data")
plt.ylabel("Temperatura Máxima (°C)")
plt.grid(False)
plt.legend()
plt.tight_layout()
plt.savefig("previsao_temperatura.png")
plt.show()
