
# 🌡️ Previsão de Temperatura Máxima com Open-Meteo

Este projeto utiliza a **API pública da Open-Meteo** para coletar a previsão da **temperatura máxima diária** nos próximos 7 dias em **quatro capitais brasileiras**:  
**São Paulo, Rio de Janeiro, Belo Horizonte e Fortaleza**.

O objetivo é demonstrar como consumir uma API REST real, transformar os dados com Python e visualizá-los com um gráfico de linha comparativo.

---

## 🚀 Tecnologias Utilizadas

- **Python 3.8+**
- `requests` – para chamadas HTTP
- `pandas` – para manipulação dos dados
- `matplotlib` – para visualização

---

## 🧠 Conceitos Aplicados

- Consumo de API pública RESTful
- Manipulação de dados em série temporal
- Merge e análise de múltiplos DataFrames
- Visualização comparativa entre cidades

---

## 🌍 Fonte dos Dados

**[Open-Meteo API](https://open-meteo.com/)**  
API pública gratuita que fornece previsão meteorológica por coordenadas geográficas. Não exige autenticação.

Exemplo de requisição usada:
```
https://api.open-meteo.com/v1/forecast?latitude=-23.55&longitude=-46.63&daily=temperature_2m_max&start_date=2024-01-01&end_date=2024-01-07&timezone=America/Sao_Paulo
```

 O que essa URL pede à API:  
latitude={lat} → localização da cidade  

longitude={lon} → idem  

daily=temperature_2m_max → queremos a temperatura máxima diária  

start_date=... e end_date=... → período de previsão (por exemplo, de hoje até daqui 7 dias)  

timezone=America/Sao_Paulo → para garantir que os horários fiquem no fuso do Brasil  

---

## 🛠️ Como Executar

1. Clone o repositório    

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. Execute o script:
   ```bash
   python meteo.py
   ```

4. O gráfico será gerado e salvo como:
   ```
   previsao_temperatura.png
   ```

---
## 💻 Código

```phyton
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

```
---

## 📊 Exemplo de Saída

![Exemplo de Gráfico de Previsão](previsao_temperatura.png)

---

## 📌 Observações

- Os dados são dinâmicos e mudam todos os dias, já que se referem à **previsão futura**.
- Você pode adaptar o código para outras cidades, basta trocar as coordenadas no dicionário `cidades`.

---

## 💡 Possíveis Extensões

- Adicionar mais cidades
- Analisar variações entre mínima e máxima
- Armazenar os dados em banco de dados ou Parquet
- Automatizar a coleta diária com agendamento (cron ou Airflow)

---

## 🧑‍💻 Autor

Projeto criado por **[Weillon Mota]**  
📫 [weillonmota@gmail.com]  
🔗 [linkedin.com/in/weillonmota](https://linkedin.com/in/weillonmota)

---
