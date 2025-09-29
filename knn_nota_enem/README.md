# 🤖 Prevendo Notas do ENEM com Machine Learning

Bem-vindo! Este projeto é um guia prático que demonstra como usar dados para treinar um modelo de Machine Learning capaz de prever as notas de um estudante no ENEM. Utilizamos uma técnica chamada **k-Nearest Neighbors (k-NN)**, ou "k-Vizinhos Mais Próximos", para realizar essa tarefa.

O objetivo é criar um material didático, explicando cada passo do processo de forma clara e simples, desde a coleta dos dados brutos até o salvamento de um modelo pronto para uso.

## 📂 Estrutura do Projeto

O código está organizado em um notebook Jupyter (`etl.ipynb`) e dividido em quatro etapas principais:

1.  **Configuração**: Onde preparamos nosso ambiente e definimos as regras do jogo.
2.  **ETL (Extração, Transformação e Carga)**: A fase de "faxina", onde limpamos e organizamos os dados.
3.  **Otimização do k-NN**: O coração do projeto, onde ensinamos o modelo a aprender com os dados.
4.  **Treinamento Final**: Onde consolidamos o aprendizado e salvamos nosso modelo inteligente.

---
## 🤔 Como o Programa Funciona? Um Guia Passo a Passo

### Etapa 1: Configuração e Constantes

Antes de começar qualquer projeto de programação, é uma boa prática organizar as ferramentas. Nesta primeira célula do código, nós:
- **Importamos as bibliotecas**: Ferramentas como `pandas` (para mexer com tabelas) e `scikit-learn` (para Machine Learning).
- **Centralizamos as informações**: Definimos nomes de arquivos e colunas em um único lugar. Isso é como ter uma "lista de compras" antes de ir ao mercado; se precisarmos mudar algo, sabemos exatamente onde olhar.

```python
# Importação de bibliotecas essenciais
import pandas as pd
import joblib
import json
import os
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsRegressor
from sklearn.metrics import mean_absolute_error

# --- ARQUIVOS E CAMINHOS ---
ARQUIVOS_ENEM = ['MICRODADOS_ENEM_2021.csv', 'MICRODADOS_ENEM_2022.csv', 'MICRODADOS_ENEM_2023.csv']
ARQUIVO_DADOS_CEARA = 'dados_ceara.csv'
ARQUIVO_MODELO = 'modelo_knn.joblib'
ARQUIVO_COLUNAS = 'colunas_modelo.json'

# --- COLUNAS DO DATASET ---
# Colunas que serão o alvo da nossa previsão (target)
COLUNAS_ALVO = ['NU_NOTA_CN', 'NU_NOTA_CH', 'NU_NOTA_LC', 'NU_NOTA_MT', 'NU_NOTA_REDACAO']
# Colunas que usaremos para fazer a previsão (features)
COLUNAS_FEATURES = ['Q006', 'Q002', 'TP_ESCOLA', 'TP_COR_RACA', 'SG_UF_ESC']
# Lista completa de colunas a serem lidas dos arquivos originais
COLUNAS_DESEJADAS = ['NU_ANO'] + COLUNAS_ALVO + COLUNAS_FEATURES

# --- PARÂMETROS DO MODELO ---
ESTADO_ALEATORIO = 42 # Garante que a divisão dos dados seja sempre a mesma
TAMANHO_TESTE = 0.2  # Define que 20% dos dados serão usados para teste

print("✅ Módulo de Configuração carregado com sucesso!")
```
> **Saída:**
> ```
> ✅ Módulo de Configuração carregado com sucesso!
> ```

### Etapa 2: A Faxina dos Dados (ETL)

Os dados brutos do ENEM são gigantescos e um pouco bagunçados. Para que nosso modelo consiga aprender algo útil, precisamos primeiro organizar a casa. O processo de ETL faz exatamente isso:

1.  **Extrair**: Lemos os arquivos CSV do ENEM (`MICRODADOS_ENEM_2021.csv`, etc.). Para não sobrecarregar a memória do computador, pegamos apenas as colunas que nos interessam.
2.  **Transformar**: Aqui acontece a mágica da limpeza. Nós:
    - Removemos todas as linhas que têm alguma informação faltando (como uma nota em branco).
    - Filtramos os dados para manter apenas os registros de estudantes do Ceará (`CE`).
3.  **Carregar**: Juntamos todos os dados limpos de diferentes anos em uma única tabela e a salvamos como `dados_ceara.csv`. Ter esse arquivo limpo economiza muito tempo, pois não precisamos repetir essa faxina toda vez que rodamos o projeto.


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
            df = pd.read_csv(arquivo, sep=';', encoding='latin-1', usecols=colunas)
            df.dropna(inplace=True)
            df_estado = df[df['SG_UF_ESC'] == estado_filtro]
            if not df_estado.empty:
                dataframes.append(df_estado)
                print(f"-> {len(df_estado)} linhas válidas encontradas.")
            else:
                print("-> Nenhuma linha válida para o Ceará neste arquivo.")
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
> --- 🚀 Iniciando processo de ETL para o estado: CE ---
> Processando: MICRODADOS_ENEM_2021.csv...
> -> 58503 linhas válidas encontradas.
> Processando: MICRODADOS_ENEM_2022.csv...
> -> 71340 linhas válidas encontradas.
> Processando: MICRODADOS_ENEM_2023.csv...
> -> 74319 linhas válidas encontradas.
>
> ✅ ETL Concluído. DataFrame final criado com 204162 linhas.
> 💾 Dados limpos salvos em 'dados_ceara.csv'.
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

1.  **Definindo os "Vizinhos" (as `COLUNAS_FEATURES`)**: Para o nosso modelo, um "vizinho" é um outro estudante com um perfil socioeconômico parecido. Nós dizemos ao algoritmo para comparar os alunos com base em características como:
    - `Q006`: A renda familiar.
    - `Q002`: A escolaridade da mãe.
    - `TP_ESCOLA`: O tipo de escola (pública ou privada).

2.  **O "k" da Questão (A Otimização do Hiperparâmetro)**: Na nossa analogia, usamos 3 casas. Mas por que 3? Por que não 5, 10 ou 20? Esse número é o `k`, e escolher o `k` certo é fundamental.
    - Se `k` for **muito pequeno** (ex: `k=1`), o modelo fica "superespecialista". Ele baseia a previsão em um único vizinho, o que pode ser muito instável e levar a erros.
    - Se `k` for **muito grande** (ex: `k=100`), o modelo fica "genérico demais". Ele considera tantos vizinhos que a previsão se torna uma média muito geral, perdendo as particularidades.

    A célula **"Otimização do Hiperparâmetro 'k'"** automatiza essa busca. Ela testa vários valores para `k` (3, 5, 7, 9, etc.) e, para cada um, calcula o **Erro Médio Absoluto (MAE)**. O MAE nos diz, em média, quão longe as previsões do modelo ficaram das notas reais. O valor de `k` que gerar o menor erro é o campeão!

3.  **O Modelo em Ação (`KNeighborsRegressor`)**: A ferramenta que usamos para isso é o `KNeighborsRegressor` do `scikit-learn`. O nome "Regressor" indica que ele serve para prever números contínuos (como uma nota de 0 a 1000), e não para classificar em categorias (como "aprovado" ou "reprovado").

```python
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsRegressor
from sklearn.metrics import mean_absolute_error
import time # Usaremos para dar uma sensação de progresso

def encontrar_melhor_k(df: pd.DataFrame, valores_k: list) -> int:
    """
    Testa diferentes valores de 'k' para o k-NN e retorna o que minimiza o erro,
    com prints detalhados do progresso.
    """
    print("\n--- 🧠 Buscando o melhor valor de 'k' para o k-NN ---")
    if df is None:
        print("❌ DataFrame de entrada é inválido. Abortando a otimização.")
        return 0

    # 1. Preparando a busca pelo melhor valor de 'k'")
    
    X = pd.get_dummies(df[COLUNAS_FEATURES], drop_first=True)
    y = df[COLUNAS_ALVO]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TAMANHO_TESTE, random_state=ESTADO_ALEATORIO
    )
    
    print("Iniciando os testes (esta etapa pode demorar)...")
    resultados_mae = {}
    for k in valores_k:
        # Print que mostra o início do teste para um 'k' específico
        print(f"   - Processando k = {k}...")
        
        # Estas são as linhas que demoram:
        modelo = KNeighborsRegressor(n_neighbors=k, n_jobs=-1)
        modelo.fit(X_train, y_train)
        y_pred = modelo.predict(X_test)
        
        # Cálculo do resultado
        mae_geral = mean_absolute_error(y_test, y_pred)
        resultados_mae[k] = mae_geral
        
        # Print que mostra o resultado parcial ao final de cada teste
        print(f"     -> Teste k={k} concluído! MAE Geral: {mae_geral:.4f}")

    # Prints finais
    melhor_k = min(resultados_mae, key=resultados_mae.get)
    print("\n   -> Todos os testes foram concluídos.")
    print(f"\n✅ Otimização Finalizada. Melhor valor encontrado: k = {melhor_k}")
    return melhor_k

# --- Execução da Função ---
# Garante que os dados existem antes de rodar
if 'dados_limpos_ceara' in locals():
    valores_k_para_testar = [3, 5, 7, 9, 11, 13, 15, 17, 19]
    melhor_k = encontrar_melhor_k(dados_limpos_ceara, valores_k_para_testar)
else:
    print("❌ ERRO: A variável 'dados_limpos_ceara' não foi encontrada. Execute a célula de ETL primeiro.")
```
> **Saída:**
> ```
> --- 🧠 Buscando o melhor valor de 'k' para o k-NN ---
> Iniciando os testes (esta etapa pode demorar)...
>    - Processando k = 3...
>      -> Teste k=3 concluído! MAE Geral: 95.0777
>    - Processando k = 5...
>      -> Teste k=5 concluído! MAE Geral: 96.2481
>    - Processando k = 7...
>      -> Teste k=7 concluído! MAE Geral: 92.9195
>    - Processando k = 9...
>      -> Teste k=9 concluído! MAE Geral: 90.2997
>    - Processando k = 11...
>      -> Teste k=11 concluído! MAE Geral: 89.7812
>    - Processando k = 13...
>      -> Teste k=13 concluído! MAE Geral: 88.5116
>    - Processando k = 15...
>      -> Teste k=15 concluído! MAE Geral: 88.0135
>    - Processando k = 17...
>      -> Teste k=17 concluído! MAE Geral: 88.0067
>    - Processando k = 19...
>      -> Teste k=19 concluído! MAE Geral: 87.9317
>
>    -> Todos os testes foram concluídos.
>
> ✅ Otimização Finalizada. Melhor valor encontrado: k = 19
> ```

### Etapa 4: Treinamento e Salvamento do Modelo Final

Depois de descobrir o melhor valor de `k`, estamos prontos para a etapa final.
1.  **Treinamento**: Nós treinamos o modelo `KNeighborsRegressor` uma última vez, usando o `k` otimizado e nosso conjunto de dados limpos.
2.  **Salvamento**: Ao final, geramos dois arquivos cruciais:
    - `modelo_knn.joblib`: Este é o nosso **modelo treinado**, como se fosse o "cérebro" do nosso sistema, pronto para fazer novas previsões.
    - `colunas_modelo.json`: Este é o **"manual de instruções"** do modelo. Ele guarda a lista exata de colunas (e a ordem delas) que o modelo precisa receber para funcionar corretamente.

Com esses dois arquivos, podemos facilmente carregar nosso modelo em outra aplicação (como um site ou um dashboard) para prever as notas de novos alunos sem precisar rodar todo o processo de limpeza e treinamento novamente.

```python
def treinar_e_salvar_modelo_final(df: pd.DataFrame, k: int):
    """
    Treina o modelo k-NN com o valor de 'k' otimizado e salva os artefatos.
    """
    print(f"\n--- 🚂 Treinando e salvando o modelo final com k = {k} ---")
    if df is None or k == 0:
        print("❌ Dados ou valor de 'k' inválidos. Abortando treinamento.")
        return

    X = pd.get_dummies(df[COLUNAS_FEATURES], drop_first=True)
    y = df[COLUNAS_ALVO]
    
    # Dica: O modelo final pode ser treinado com todos os dados, mas para manter
    # a consistência do projeto, vamos usar o mesmo split.
    X_train, _, y_train, _ = train_test_split(
        X, y, test_size=TAMANHO_TESTE, random_state=ESTADO_ALEATORIO
    )

    modelo_final = KNeighborsRegressor(n_neighbors=k, n_jobs=-1)
    modelo_final.fit(X_train, y_train)

    joblib.dump(modelo_final, ARQUIVO_MODELO)
    with open(ARQUIVO_COLUNAS, 'w') as f:
        json.dump(X.columns.tolist(), f)

    print(f"✅ Modelo final treinado com sucesso!")
    print(f"💾 Modelo salvo em: '{ARQUIVO_MODELO}'")
    print(f"💾 Colunas salvas em: '{ARQUIVO_COLUNAS}'")
    print("\n--- 🚀 PROJETO CONCLUÍDO ---")

# Executa o treinamento final com o melhor 'k' encontrado
treinar_e_salvar_modelo_final(dados_limpos_ceara, melhor_k)
```
> **Saída:**
> ```
> --- 🚂 Treinando e salvando o modelo final com k = 19 ---
> ✅ Modelo final treinado com sucesso!
> 💾 Modelo salvo em: 'modelo_knn.joblib'
> 💾 Colunas salvas em: 'colunas_modelo.json'
>
> --- 🎉 PROJETO FINALIZADO ---
> ```

## ✨ Sessão Bônus: A Aplicação Prática em um Dashboard Interativo

Após todo o trabalho de limpeza, otimização e treinamento, o produto final não é apenas o código, mas o modelo salvo (modelo_knn.joblib) e seu manual (colunas_modelo.json), prontos para serem usados.

O Dashboard interativo é a prova de conceito de que nosso modelo funciona na prática. Ele permite que qualquer pessoa interaja com o "cérebro" do Machine Learning que acabamos de criar.

## 📊 Objetivo do Dashboard
O objetivo é transformar a lógica complexa do nosso código Python em uma ferramenta acessível e visual. O dashboard, implementado no arquivo dashboard.py (em anexo no repositório), faz o seguinte:

- Carrega o Modelo e o Manual: Ele usa o joblib para carregar o modelo_knn.joblib e o json para carregar as colunas necessárias.  

- Coleta o Perfil do Usuário: Ele apresenta widgets simples para o usuário informar suas características socioeconômicas (Q006, Q002, TP_ESCOLA, etc.) – exatamente as COLUNAS_FEATURES que o modelo espera.  

- Realiza a Previsão: Ele insere as informações do usuário no modelo e recebe as notas previstas nas cinco áreas do conhecimento (COLUNAS_ALVO).  

- Exibe os Resultados: Ele apresenta as notas previstas de forma clara e visual, provando que o processo de ponta a ponta (ETL, Treinamento, Produção) foi bem-sucedido.  

## 🎨 Sobre o Streamlit
Para construir o dashboard, utilizamos a biblioteca Streamlit.

O Streamlit é uma ferramenta de código aberto que permite transformar scripts de análise de dados e Machine Learning em aplicativos da web interativos e bonitos com pouquíssimas linhas de código. É a solução perfeita para demonstrar o potencial do nosso modelo sem a necessidade de aprender tecnologias complexas de desenvolvimento web (como HTML, CSS e JavaScript). Ele lida com a interatividade, o layout e a implantação de forma quase mágica.  

## 🔗 Veja o Modelo em Ação
Você pode interagir e testar o poder de previsão do modelo k-NN treinado neste projeto através do link de implantação:  

[Veja o projeto clicando aqui!](https://projetos-262dc3bahjdyph3gmfuexf.streamlit.app/)

## 🧑‍💻 Autor

Projeto criado por **[Weillon Mota]**  
📫 [weillonmota@gmail.com]  
🔗 [linkedin.com/in/weillonmota](https://linkedin.com/in/weillonmota)
