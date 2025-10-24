# 🤖 Prevendo Notas do ENEM com Machine Learning

Bem-vindo! Este projeto é um guia prático que demonstra como usar dados para treinar um modelo de Machine Learning otimizado capaz de prever as notas de um estudante no ENEM.

Utilizamos uma técnica chamada k-Nearest Neighbors (k-NN), ou "k-Vizinhos Mais Próximos", e aplicamos a Normalização de Features (StandardScaler) e os Pesos por Distância (weights='distance') para aumentar a precisão e a qualidade da previsão.

O objetivo é criar um material didático, explicando cada passo do processo de forma clara e simples, desde a coleta dos dados brutos até o salvamento de um modelo robusto e pronto para uso em uma aplicação web.

## 📂 Estrutura do Projeto

O código está organizado em um notebook Jupyter (`etl.ipynb`) e dividido em quatro etapas principais:

1.  **Configuração**: Onde preparamos nosso ambiente e definimos as regras do jogo.
2.  **ETL (Extração, Transformação e Carga)**: A fase de "faxina", onde limpamos e organizamos os dados.
3.  **Otimização do k-NN**: O coração do projeto, onde testamos o melhor hiperparâmetro `k` usando uma técnica de pesos por distância para previsões mais inteligentes.
4.  **Treinamento Final e Salvamento de Artefatos**: Onde consolidamos o aprendizado e salvamos todos os arquivos necessários para a aplicação (`modelo.joblib`, `scaler.joblib`, `colunas.json` e `y_train_data.csv`).

---
## 🤔 Como o Programa Funciona? Um Guia Passo a Passo

### Etapa 1: Configuração e Constantes

Antes de começar qualquer projeto de programação, é uma boa prática organizar as ferramentas. Nesta primeira célula do código, é preciso:
- **Importamos as bibliotecas**: Ferramentas como `pandas` (para mexer com tabelas), `scikit-learn` (para Machine Learning) e `StandardScaler`para normalizar nossos dados.
- **Centralizamos as informações**: Definimos nomes de arquivos e colunas em um único lugar. Isso é como ter uma "lista de compras" antes de ir ao mercado e se precisarmos mudar algo, sabemos exatamente onde olhar. Temos arquivos: `ARQUIVO_SCALER` (para salvar nosso normalizador) e `ARQUIVO_Y_TRAIN` (para salvar os dados de treino, permitindo a comparação com os vizinhos no dashboard).

```python
# Importação de bibliotecas essenciais
import pandas as pd
import joblib
import json
import os
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.preprocessing import StandardScaler  # <-- Para normalizar os dados

# --- ARQUIVOS E CAMINHOS ---
ARQUIVOS_ENEM = ['MICRODADOS_ENEM_2021.csv', 'MICRODADOS_ENEM_2022.csv', 'MICRODADOS_ENEM_2023.csv']
ARQUIVO_DADOS_CEARA = 'dados_ceara.csv'
ARQUIVO_MODELO = 'modelo_knn.joblib'
ARQUIVO_COLUNAS = 'colunas_modelo.json'
ARQUIVO_SCALER = 'scaler.joblib'       # <-- Arquivo para o normalizador
ARQUIVO_Y_TRAIN = 'y_train_data.csv'  # <-- Arquivo para os dados de treino

# --- COLUNAS DO DATASET ---
COLUNAS_ALVO = ['NU_NOTA_CN', 'NU_NOTA_CH', 'NU_NOTA_LC', 'NU_NOTA_MT', 'NU_NOTA_REDACAO']
COLUNAS_FEATURES = ['Q006', 'Q002', 'TP_ESCOLA', 'TP_COR_RACA', 'SG_UF_ESC']
COLUNAS_DESEJADAS = ['NU_ANO'] + COLUNAS_ALVO + COLUNAS_FEATURES

# --- PARÂMETROS DO MODELO ---
ESTADO_ALEATORIO = 42 
TAMANHO_TESTE = 0.2  

print("✅ Módulo de Configuração (v2) carregado com sucesso!")
```
> **Saída:**
> ```
> ✅ Módulo de Configuração carregado com sucesso!
> ```

### Etapa 2: A Faxina dos Dados (ETL)

Os dados brutos do ENEM são gigantescos e um pouco bagunçados. Para que nosso modelo consiga aprender algo útil, precisamos primeiro organizar a casa. O processo de ETL faz exatamente isso:

1.  **Extrair**: Lemos os arquivos CSV (um para cada ano). Para não sobrecarregar a memória do computador, lemos apenas as colunas que definimos no Bloco 1 (`COLUNAS_DESEJADAS`).
   
2.  **Transformar**: Aqui acontece a mágica da limpeza. Nós:
    - **Removemos** todas as linhas que têm alguma informação faltando (ex: dropna()). Um aluno sem nota não pode ser usado para treinar o modelo.
    - **Filtramos** os dados para manter apenas os registros de estudantes do Ceará (CE), conforme definido em `estado_filtro`.
    - **Tratamos erros** de codificação, tentando ler os arquivos em latin-1 e, se falhar, mudando para utf-8.
      
3.  **Carregar**: Juntamos todos os dados limpos de diferentes anos em uma única tabela e a salvamos como `dados_ceara.csv`. Ter esse arquivo limpo economiza muito tempo, pois não precisamos repetir essa faxina toda vez que rodamos o projeto.

**⚠️ Observação Importante sobre a Amostragem:**  
*Para diminuir o universo de dados e focar a análise em um contexto específico, optamos por limitar a amostragem a estudantes do Ceará (CE). No entanto, para compensar essa redução e aumentar a robustez do modelo, incluímos um período maior de tempo, utilizando as notas do ENEM de três anos (2021 a 2023). O objetivo desse balanceamento é fornecer uma base sólida o suficiente para melhorar o índice MAE (Erro Médio Absoluto), a métrica de erro que será detalhada na seção de treinamento do modelo k-NN.* 

Base de Dados: Microdados do ENEM  
Local de Acesso: [https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem)

```python
def executar_etl(lista_arquivos: list, colunas: list, estado_filtro: str = 'CE') -> pd.DataFrame | None:
    """
    Lê, limpa, filtra e combina múltiplos arquivos CSV do ENEM.
    - Extração: Lê apenas as colunas desejadas para otimizar o uso de memória.
    - Transformação: Remove linhas com dados faltantes e filtra pelo estado.
    - Carga: Consolida os dados de todos os arquivos em um único DataFrame.
    """
    print(f"\n--- 🚀 Iniciando processo de ETL para o estado: {estado_filtro} ---")
    dataframes = []

    for arquivo in lista_arquivos:
        if not os.path.exists(arquivo):
            print(f"⚠️ AVISO: Arquivo '{arquivo}' não encontrado. Pulando...")
            continue
        try:
            print(f"Processando: {arquivo}...")
            # Tentando com encoding 'latin-1' como no original
            try:
                df = pd.read_csv(arquivo, sep=';', encoding='latin-1', usecols=colunas)
            except UnicodeDecodeError:
                print(f"-> Falha no latin-1. Tentando 'utf-8' para {arquivo}...")
                df = pd.read_csv(arquivo, sep=';', encoding='utf-8', usecols=colunas)
                
            df.dropna(inplace=True)
            df_estado = df[df['SG_UF_ESC'] == estado_filtro]
            
            if not df_estado.empty:
                dataframes.append(df_estado)
                print(f"-> {len(df_estado)} linhas válidas encontradas.")
            else:
                print(f"-> Nenhuma linha válida para o Ceará neste arquivo.")
                
        except Exception as e:
            print(f"❌ ERRO inesperado ao processar '{arquivo}': {e}")

    if not dataframes:
        print("\n❌ ETL falhou. Nenhum DataFrame foi processado.")
        return None

    df_final = pd.concat(dataframes, ignore_index=True)
    print(f"\n✅ ETL Concluído. DataFrame final criado com {len(df_final)} linhas.")
    df_final.to_csv(ARQUIVO_DADOS_CEARA, index=False)
    print(f"💾 Dados limpos salvos em '{ARQUIVO_DADOS_CEARA}'.")
    return df_final

# Executa a função
dados_limpos_ceara = executar_etl(lista_arquivos=ARQUIVOS_ENEM, colunas=COLUNAS_DESEJADAS)
```
> **Saída:**
> ```
>--- 🚀 Iniciando processo de ETL para o estado: CE ---
Processando: MICRODADOS_ENEM_2021.csv...
-> 58503 linhas válidas encontradas.
Processando: MICRODADOS_ENEM_2022.csv...
-> 71340 linhas válidas encontradas.
Processando: MICRODADOS_ENEM_2023.csv...
-> 74319 linhas válidas encontradas.

✅ ETL Concluído. DataFrame final criado com 204162 linhas.
💾 Dados limpos salvos em 'dados_ceara.csv'.
> ```

### Etapa 3: Ensinando o Computador a "Adivinhar" com k-NN

Agora chegamos à parte mais interessante: como o modelo de Machine Learning realmente funciona? Usamos o algoritmo **k-Nearest Neighbors (k-NN)**, que é surpreendentemente intuitivo.

#### Uma Analogia Simples para Entender o k-NN

Imagine que você quer prever o preço de uma casa, mas não tem ideia de como fazer isso. Uma abordagem simples seria:
1.  Encontrar as **3 casas mais parecidas** com a sua na mesma vizinhança (com tamanho, número de quartos e idade similares).
2.  Perguntar o preço de cada uma dessas 3 casas.
3.  Calcular a **média de preço** dessas 3 casas.
4.  Pronto! Essa média é a sua "previsão" para o preço da sua casa.

O k-NN faz exatamente isso, mas para prever as notas do ENEM. Ele não prevê o preço de uma casa, mas sim as notas de um aluno (`NU_NOTA_CN`, `NU_NOTA_MT`, etc.).

#### Como o k-NN Foi Implementado Neste Projeto?

A ferramenta que usamos para isso é o KNeighborsRegressor do scikit-learn . O nome "Regressor" indica que ele serve para prever números contínuos (como uma nota de 0 a 1000), e não para classificar em categorias (como "aprovado" ou "reprovado").


Para o modelo funcionar, nós definimos:

1.  **Definindo os "Vizinhos" (as `COLUNAS_FEATURES`)**: Para o nosso modelo, um "vizinho" é um outro estudante com um perfil socioeconômico parecido. Nós dizemos ao algoritmo para comparar os alunos com base em características como:
    - `Q006`: A renda familiar.
    - `Q002`: A escolaridade da mãe.
    - `TP_ESCOLA`: O tipo de escola (pública ou privada).

2.  **O "k" da Questão (A Otimização do Hiperparâmetro)**: Na nossa analogia, usamos 3 casas. Mas por que 3? Por que não 5, 10 ou 20? Esse número é o `k`, e escolher o `k` certo é fundamental.
    - Se `k` for **muito pequeno** (ex: `k=1`), o modelo fica "superespecialista". Ele baseia a previsão em um único vizinho, o que pode ser muito instável e levar a erros.
    - Se `k` for **muito grande** (ex: `k=100`), o modelo fica "genérico demais". Ele considera tantos vizinhos que a previsão se torna uma média muito geral, perdendo as particularidades.

    A célula **"Otimização do Hiperparâmetro 'k'"** automatiza essa busca. Ela testa vários valores para `k` (3, 5, 7, 9, etc.) e, para cada um, calcula o **Erro Médio Absoluto (MAE)**. O MAE nos diz, em média, quão longe as previsões do modelo ficaram das notas reais. O valor de `k` que gerar o menor erro é o campeão!

3.  **O Modelo em Ação (`KNeighborsRegressor`)**: A ferramenta que usamos para isso é o `KNeighborsRegressor` do `scikit-learn`. O nome "Regressor" indica que ele serve para prever números contínuos (como uma nota de 0 a 1000), e não para classificar em categorias (como "aprovado" ou "reprovado").

Para garantir que o modelo seja justo e inteligente, aplicamos essas técnicas:
4. **Normalização de Features** (StandardScaler): Nossos dados (COLUNAS_FEATURES) têm escalas muito diferentes (ex: Renda, com muitas categorias, vs. Tipo de Escola, com apenas duas). Para que o modelo calcule a "distância" de forma justa, sem que uma feature domine a outra, nós normalizamos os dados. O StandardScaler faz com que todas as features tenham a mesma escala de importância.

5. **Pesos por Distância** (weights='distance'): Em vez de tratar todos os "vizinhos" como iguais, usamos weights='distance'. Isso diz ao modelo para dar mais peso aos vizinhos que são extremamente parecidos e menos peso aos que são apenas "mais ou menos" parecidos. Isso resulta em uma previsão muito mais precisa e sensível às pequenas diferenças de perfil.

A função `encontrar_melhor_k` no código abaixo implementa tudo isso:

```python
def encontrar_melhor_k(df: pd.DataFrame, valores_k: list) -> int:
    """
    Testa diferentes valores de 'k' para o k-NN (usando weights='distance')
    e retorna o que minimiza o erro.
    """
    print("\n--- 🧠 Buscando o melhor valor de 'k' (com StandardScaler e weights='distance') ---")
    if df is None:
        print("❌ DataFrame de entrada é inválido. Abortando a otimização.")
        return 0

    X = pd.get_dummies(df[COLUNAS_FEATURES], drop_first=True)
    y = df[COLUNAS_ALVO]
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TAMANHO_TESTE, random_state=ESTADO_ALEATORIO
    )

    print("Aplicando StandardScaler (normalização)...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    print("-> Dados normalizados.")
    
    print("Iniciando os testes (esta etapa pode demorar)...")
    resultados_mae = {}
    for k in valores_k:
        print(f"   - Processando k = {k}...")
        
        # --- MODIFICAÇÃO PRINCIPAL AQUI ---
        # Adicionamos weights='distance'
        modelo = KNeighborsRegressor(
            n_neighbors=k, 
            weights='distance', # <-- A MUDANÇA
            n_jobs=-1
        ) 
        # ------------------------------------
        
        modelo.fit(X_train_scaled, y_train)
        y_pred = modelo.predict(X_test_scaled) 

        mae_geral = mean_absolute_error(y_test, y_pred)
        resultados_mae[k] = mae_geral
        
        print(f"     -> Teste k={k} concluído! MAE Geral: {mae_geral:.4f}")

    if not resultados_mae:
        print("❌ Nenhum resultado foi calculado. Verifique os dados de entrada.")
        return 0
        
    melhor_k = min(resultados_mae, key=resultados_mae.get)
    print("\n   -> Todos os testes foram concluídos.")
    # O MAE pode ser um pouco diferente agora, o que é normal
    print(f"\n✅ Otimização Finalizada. Melhor valor encontrado: k = {melhor_k}")
    return melhor_k

# --- Execução da Função ---
if 'dados_limpos_ceara' in locals() and dados_limpos_ceara is not None:
    valores_k_para_testar = [3, 5, 7, 9, 11, 13, 15, 17, 19]
    melhor_k = encontrar_melhor_k(dados_limpos_ceara, valores_k_para_testar)
else:
    print("❌ ERRO: A variável 'dados_limpos_ceara' não foi encontrada ou está vazia.")
    print("➡️ Por favor, execute a célula de ETL (Bloco 2) primeiro.")
    melhor_k = 0ão foi encontrada. Execute a célula de ETL primeiro.")
```

> **Saída:**
> ```
> --- 🧠 Buscando o melhor valor de 'k' (com StandardScaler e weights='distance') ---
Aplicando StandardScaler (normalização)...
-> Dados normalizados.
Iniciando os testes (esta etapa pode demorar)...
   - Processando k = 3...
     -> Teste k=3 concluído! MAE Geral: 96.4514
   - Processando k = 5...
     -> Teste k=5 concluído! MAE Geral: 91.9658
   - Processando k = 7...
     -> Teste k=7 concluído! MAE Geral: 91.3061
   - Processando k = 9...
     -> Teste k=9 concluído! MAE Geral: 89.2031
   - Processando k = 11...
     -> Teste k=11 concluído! MAE Geral: 88.3925
   - Processando k = 13...
     -> Teste k=13 concluído! MAE Geral: 87.6376
   - Processando k = 15...
     -> Teste k=15 concluído! MAE Geral: 87.4599
   - Processando k = 17...
     -> Teste k=17 concluído! MAE Geral: 87.2849
   - Processando k = 19...
     -> Teste k=19 concluído! MAE Geral: 86.8260

   -> Todos os testes foram concluídos.

✅ Otimização Finalizada. Melhor valor encontrado: k = 19
> ```

### Etapa 4: Treinamento e Salvamento do Modelo Final

Depois de todo o trabalho de limpeza (Etapa 2) e otimização (Etapa 3), descobrimos que k=19 é o nosso número ideal de vizinhos.

Agora, estamos prontos para treinar o modelo uma última vez e salvá-lo. Esta etapa é crucial, pois ela gera os "artefatos" — os arquivos finais que nosso dashboard (ou qualquer outra aplicação) usará para fazer previsões reais.

Nós não salvamos apenas o modelo, mas quatro arquivos essenciais:

1. `modelo_knn.joblib`: Este é o "cérebro" do nosso sistema. É o modelo k-NN treinado com o k=19 e weights='distance'.

2. `scaler.joblib`: Este é o "normalizador" oficial. Ele salvou a média e o desvio padrão dos nossos dados de treino. Qualquer nova informação (como a de um usuário no dashboard) deve ser normalizada por este exato scaler para que a previsão funcione.

3. `colunas_modelo.json`: Este é o "manual de instruções" do modelo. Ele salva a lista exata de colunas (e a ordem delas) que o modelo foi treinado para receber. Isso evita erros se o usuário inserir dados em ordem diferente.

4. `y_train_data.csv`: Este é o nosso "banco de dados dos vizinhos". Ele contém as notas reais de todos os alunos que o modelo usou para treinar. O dashboard usará este arquivo para encontrar as notas mínimas, máximas e médias dos vizinhos e compará-las com a previsão.

A função treinar_e_salvar_modelo_final faz exatamente isso: ela treina o modelo com os dados de treino e salva esses quatro artefatos no disco.

```python
def treinar_e_salvar_modelo_final(df: pd.DataFrame, k: int):
    """
    Treina o modelo k-NN com 'weights=distance' e salva todos os artefatos.
    """
    print(f"\n--- 🚂 Treinando e salvando o modelo final com k = {k} e weights='distance' ---")
    if df is None or k == 0:
        print("❌ Dados ou valor de 'k' inválidos. Abortando treinamento.")
        return

    # 1. Preparar os dados
    X = pd.get_dummies(df[COLUNAS_FEATURES], drop_first=True)
    y = df[COLUNAS_ALVO]
    
    X_train, _, y_train, _ = train_test_split(
        X, y, test_size=TAMANHO_TESTE, random_state=ESTADO_ALEATORIO
    )

    # 2. StandardScaler
    print("Aplicando e salvando o StandardScaler...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    print("-> Scaler treinado.")

    # 3. Treina o modelo final
    print("Treinando o modelo k-NN final...")
    
    # --- MODIFICAÇÃO PRINCIPAL AQUI ---
    modelo_final = KNeighborsRegressor(
        n_neighbors=k, 
        weights='distance', # <-- A MUDANÇA
        n_jobs=-1
    )
    # ------------------------------------
    
    modelo_final.fit(X_train_scaled, y_train) 
    print("-> Modelo treinado.")

    # 4. Salvando os artefatos
    print("Salvando artefatos no disco...")
    
    joblib.dump(modelo_final, ARQUIVO_MODELO)
    joblib.dump(scaler, ARQUIVO_SCALER) 
    
    with open(ARQUIVO_COLUNAS, 'w') as f:
        json.dump(X_train.columns.tolist(), f) 

    # Salva o y_train (sem mudanças aqui)
    y_train.reset_index(drop=True).to_csv(ARQUIVO_Y_TRAIN, index=False)

    print(f"✅ Modelo final treinado com sucesso!")
    print(f"💾 Modelo salvo em: '{ARQUIVO_MODELO}' (com weights='distance')")
    print(f"💾 Scaler salvo em: '{ARQUIVO_SCALER}'") 
    print(f"💾 Colunas salvas em: '{ARQUIVO_COLUNAS}'")
    print(f"💾 Dados de treino (y_train) salvos em: '{ARQUIVO_Y_TRAIN}'")
    print("\n--- 🚀 PROJETO CONCLUÍDO ---")

# --- Execução da Função ---
if 'dados_limpos_ceara' in locals() and 'melhor_k' in locals():
    if dados_limpos_ceara is not None and melhor_k > 0:
        treinar_e_salvar_modelo_final(dados_limpos_ceara, melhor_k)
    else:
        print("❌ ERRO: 'dados_limpos_ceara' ou 'melhor_k' são inválidos. Verifique os blocos anteriores.")
else:
    print("❌ ERRO: Variáveis 'dados_limpos_ceara' ou 'melhor_k' não encontradas. Execute os Blocos 2 e 3.")
```
> **Saída:**
> ```
>--- 🚂 Treinando e salvando o modelo final com k = 19 e weights='distance' ---
Aplicando e salvando o StandardScaler...
-> Scaler treinado.
Treinando o modelo k-NN final...
-> Modelo treinado.
Salvando artefatos no disco...
✅ Modelo final treinado com sucesso!
💾 Modelo salvo em: 'modelo_knn.joblib' (com weights='distance')
💾 Scaler salvo em: 'scaler.joblib'
💾 Colunas salvas em: 'colunas_modelo.json'
💾 Dados de treino (y_train) salvos em: 'y_train_data.csv'
--- 🚀 PROJETO CONCLUÍDO ---
> ```

## ✨ Sessão Bônus: Aplicação Prática em um Dashboard Interativo  

Após todo o trabalho de limpeza, otimização e treinamento, o produto final não é apenas o código, mas o modelo salvo (`modelo_knn.joblib`) e seu manual (`colunas_modelo.json`), prontos para serem usados.

O Dashboard interativo é a prova de conceito de que nosso modelo funciona na prática. Ele permite que qualquer pessoa interaja com o "cérebro" do Machine Learning que acabamos de criar.

## 📊 Objetivo do Dashboard  
O objetivo é transformar a lógica complexa do nosso código Python em uma ferramenta acessível e visual. O dashboard, implementado no arquivo `dashboard.py` (em anexo no repositório), faz o seguinte:

- Carrega os 4 artefatos (modelo_knn.joblib, scaler.joblib, colunas_modelo.json e y_train_data.csv).
- Coleta o Perfil do Usuário através de caixas de seleção (Renda, Escolaridade da Mãe, etc.).
- Prepara os dados do usuário: Converte as escolhas em um formato que o modelo entenda (usando `get_dummies` e `reindex` com as colunas salvas).
- Normaliza os dados: Aplica o `scaler.joblib` nos dados do usuário.
- Realiza a Previsão: Passa os dados normalizados para o `modelo_knn.joblib` e obtém as notas previstas.
- Compara com os Vizinhos: O dashboard usa a previsão para encontrar os `k` vizinhos no arquivo `y_train_data.csv` e exibe a comparação da nota do aluno com a média, mínima e máxima do seu grupo de perfil similar.

## 🎨 Sobre o Streamlit  
Para construir o dashboard, utilizamos a biblioteca Streamlit.

O Streamlit é uma ferramenta de código aberto que permite transformar scripts de análise de dados e Machine Learning em aplicativos da web interativos e bonitos com pouquíssimas linhas de código. É a solução perfeita para demonstrar o potencial do nosso modelo sem a necessidade de aprender tecnologias complexas de desenvolvimento web (como HTML, CSS e JavaScript). Ele lida com a interatividade, o layout e a implantação de forma quase mágica.  

## 🎯 Veja o Modelo em Ação  
Você pode interagir e testar o poder de previsão do modelo k-NN treinado neste projeto através do link de implantação:  

👉[Veja o projeto clicando aqui!](https://enem-knn.streamlit.app/)

## 🚀 Conclusão  
Este projeto transforma dados brutos em inteligência acionável. Seguindo estes passos, construímos um sistema que aprendeu a encontrar padrões no perfil dos estudantes e, com base neles, fazer previsões sobre seu desempenho no ENEM. O uso do k-NN mostra como conceitos de "similaridade" e "vizinhança" podem ser ferramentas poderosas no mundo do Machine Learning.

## 🧑‍💻 Autor

Projeto criado por **[Weillon Mota]**  
📫 [weillonmota@gmail.com]  
🔗 [linkedin.com/in/weillonmota](https://linkedin.com/in/weillonmota)
