# 🏥 Projeto: Data Lake Hospital Universitário Onofre Lopes

## 🎯 Visão Geral do Projeto

Este projeto visa dar um suporte ao **Hospital Universitário Onofre Lopes (HUOL)** em Natal/RN com objetivo de estudar a concorrência das internações e analisar a reputação do Hospital no Instagram.

Vamos cruzar dois tipos de dados: o **estruturado** (dados de internações históricas do SUS) com o **não estruturado** comentários postados na página do Hospital no Instagram para extrair insights valiosos, usando **Machine Learning** e **análise estatística**, para apoiar a decisão estratégica de expansão do serviço de internação.

----------

## 🛠️ Fase 1: Data Lake, Infra e Ingestão Bruta (Bronze)

A primeira camada do Data Lake é a **Bronze** que prepara o ambiente para receber os dados brutos.

### 1. Configuração da Infraestrutura (AWS S3)

-   **Onde Guardamos a Bagunça:** Escolhemos o **Amazon S3 (Simple Storage Service)**, o _storage_ de objetos padrão de mercado, utilizando o **Free Tier** da AWS para garantir escalabilidade e durabilidade a custo zero na largada.
    
-   **Estrutura:** Criamos o _bucket_ (`datalake-sad-huol-weillon`) e organizamos a arquitetura do Data Lake em três camadas, seguindo as melhores práticas:
    
    -   `/bronze`: **Dados Brutos** (raw data).
        
    -   `/silver`: **Dados Limpos/Enriquecidos** (prontos para análise).
        
    -   `/gold`: **Data Warehouse (DW)** modelado (tabela Fato e Dimensões).
        

### 2. Acesso Seguro e Mínimo (IAM)

A segurança é _prioridade zero_! Bloqueamos o acesso público ao _bucket_ e criamos um mecanismo seguro para o nosso código interagir com o S3.

-   **Princípio:** Aplicamos o **Princípio do Menor Privilégio (PoLP)**.
    
-   **Usuário Programático:** Criamos o usuário IAM (`user-projeto-sad-huol`) para uso em código local.
    
-   **Política Customizada:** Anexamos a política **`Policy-SAD-HUOL-S3-Acesso-Mínimo`**. Esta política restringe o acesso _apenas_ ao nosso _bucket_ específico e permite **somente** as ações necessárias (`ListBucket`, `GetObject`, `PutObject`).
    



Abaixo, o _screenshot_ da política customizada criada no console IAM, garantindo a restrição de acesso ao S3.

![Políticas IAM](./evidencias/001.jpg)

### 3. Coleta e Ingestão de Dados Estruturados (SUS)

Os dados estruturados do HUOL foram coletados no portal do Governo Federal, exigindo autenticação `gov.br` para _download_.

-   **Fonte:** Base de **Internações Hospitalares** do HUOL/UFRN.
    
-   **Período:** Janeiro de 2024 a Setembro de 2025.
    
-   **Ingestão Bronze:** Os 7 arquivos CSV brutos foram carregados na camada de entrada do nosso Data Lake.
    

#### **[Visualização 2: Evidência da Camada Bronze]**

Aqui está o _screenshot_ do _bucket_ S3, demonstrando a presença dos 7 arquivos CSV brutos de internações na pasta `/bronze`.

![bucket S3](/evidencias/002.jpg)


### 4. Coleta de Dados Não Estruturados (Web Scraping com Selenium)

Para complementar a camada bronze é preciso coletar os dados do Instagram do Hospital. Inicialmente tentamos o utilizar o API da própria META, porém sem êxito, devido a complexidade da autenticação e restrições de permissão, foi necessario mudar de estratégia para uma solução robusta de **Web Scraping** para a coleta dos comentários na página do Hospital. Após coletar os dados brutos do instagram conseguimos subir esses dados para o S3 na Amazon finalizando assim nossa camada bronze.

-   **Vantagem:** O **Selenium** simula um usuário logado no navegador Firefox, garantindo a coleta de todos os comentários públicos e superando a complexidade das permissões da API.
    
-   **Segurança:** Implementamos a leitura segura de credenciais via arquivo **`.env`**, garantindo que a senha de acesso (necessária para o login do Selenium) não seja exposta no código.
    

----------

Segue abaixo o codigo do scraper que foi utilizado para coletar os dados do instagram do hospital.

## 💻 Código do Scraper (coleta_instagram.py)

O script mapeia e extrai os dados do perfil do HUOL e salva as informações no formato CSV (que é o formato final que será carregado no S3).

_Pré-requisitos:_ `pip install selenium webdriver-manager python-dotenv`

Python

```
import csv
import time
import os
from typing import List, Dict, Any, Set
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDriver
from dotenv import load_dotenv

# --- CARREGAR VARIÁVEIS DE AMBIENTE (.env) ---
# Garante que as credenciais sensíveis não fiquem expostas no código.
load_dotenv() 

# --- CONFIGURAÇÕES DO SCRAPER (Lidas do .env) ---
INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME") 
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD") 
TARGET_PROFILE = "https://www.instagram.com/huol_ufrn/"
CSV_FILENAME = "comentarios_huol_completo_223posts.csv"

# --- CLASSE PRINCIPAL ---
class InstagramCommentScraper:
    # O construtor recebe as credenciais (que vieram do .env)
    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password
        self.driver = self._setup_driver()
        self.wait = WebDriverWait(self.driver, 20) 

    def _setup_driver(self) -> WebDriver:
        # Configuração do Selenium para usar o Firefox
        firefox_options = Options()
        # firefox_options.add_argument("--headless") # Descomentar para rodar em modo invisível
        service = Service(GeckoDriverManager().install()) # Garante o driver mais recente
        return webdriver.Firefox(service=service, options=firefox_options)

    def login(self) -> None:
        """Realiza o login automatizado no Instagram."""
        print("🔐 Fazendo Login...")
        self.driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(5)
        try:
            try: self.driver.find_element(By.XPATH, "//button[text()='Allow all cookies' or text()='Permitir todos os cookies']").click()
            except: pass
            
            # Preenche nome de usuário e senha, lidos do .env
            self.wait.until(EC.element_to_be_clickable((By.NAME, "username"))).send_keys(self.username)
            time.sleep(1)
            self.driver.find_element(By.NAME, "password").send_keys(self.password)
            time.sleep(1)
            
            # Clica no botão de login
            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            
            # Espera carregar a página inicial para confirmar o sucesso
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "svg[aria-label='Home'], svg[aria-label='Página inicial']")))
            print("✅ Login realizado com sucesso.")
            time.sleep(5)
        except Exception as e:
            print(f"❌ Falha no login. Verifique as credenciais no .env. Erro: {e}")
            self.driver.quit(); exit()

    def get_all_post_links(self, profile_url: str, target_count: int = 300) -> List[str]:
        """Rola a página do perfil para mapear URLs de posts."""
        print(f"🔍 Mapeando posts do perfil: {profile_url}")
        self.driver.get(profile_url)
        time.sleep(5)
        
        post_links: Set[str] = set()
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        tentativas_sem_novos = 0
        
        print("   🔄 Rolando perfil para carregar posts antigos...")
        
        # Loop de rolagem para carregar dinamicamente mais posts
        while len(post_links) < target_count:
            # Coleta todos os links de posts visíveis (URLs com '/p/')
            anchors = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/p/')]")
            for anchor in anchors:
                href = anchor.get_attribute("href")
                if href: post_links.add(href)
            
            print(f"      -> {len(post_links)} posts encontrados...")
            
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3) 
            
            # Lógica para sair do loop se chegar ao fim da página
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                tentativas_sem_novos += 1
                if tentativas_sem_novos >= 3: 
                    print("   ✅ Fim da página de perfil (Não há mais posts para carregar).")
                    break
            else:
                tentativas_sem_novos = 0
                last_height = new_height
                
        lista_final = list(post_links)
        print(f"📌 Mapeamento concluído: {len(lista_final)} posts prontos para extração.")
        return lista_final

    def extract_comments_from_post(self, post_url: str) -> List[Dict[str, Any]]:
        """Acessa o post, carrega e extrai dados dos comentários."""
        print(f"\n📥 Acessando: {post_url}")
        self.driver.get(post_url)
        time.sleep(5) 
        
        extracted_data: List[Dict[str, Any]] = []
        seen_comments: Set[tuple] = set()
        
        try:
            post_id = post_url.split("/p/")[1].split("/")[0]
        except: post_id = "post_unk"

        try:
            li_elements = self.driver.find_elements(By.XPATH, "//ul//li")
            count_inicial = len(li_elements)
            
            # --- LÓGICA HÍBRIDA (Intervenção Manual para posts grandes) ---
            if count_inicial > 17: 
                print("   🚨 POST GRANDE! Necessário carregar manualmente.")
                print("   👉 Role a barra de comentários no Firefox até o fim.")
                input("   👉 Pressione ENTER aqui quando terminar de carregar TUDO...") # Pausa a execução
                print("   🤖 Ok! Capturando dados...")
                
                # Atualiza a lista após rolagem manual do usuário
                li_elements = self.driver.find_elements(By.XPATH, "//ul//li")
            
            # --- EXTRAÇÃO ---
            for li in li_elements:
                try:
                    full_text = li.text.strip()
                    lines = full_text.split('\n')
                    
                    autor = "Desconhecido"
                    if lines: autor = lines[0].strip()
                    
                    # Ignora a legenda do post e elementos de interface
                    is_legenda = False
                    try:
                        if li.find_element(By.TAG_NAME, "h1"): is_legenda = True
                    except: pass
                    if is_legenda: continue 

                    texto_parts = []
                    # Blacklist de termos de interface do usuário
                    blacklist = ["Responder", "Reply", "Enviar", "Editado", "Ver insights", "Ocultar", autor]
                    
                    for line in lines:
                        l = line.strip()
                        if l in blacklist: continue 
                        if "curtida" in l or "like" in l: continue 
                        texto_parts.append(l)
                        
                    texto_final = " ".join(texto_parts).strip()

                    # Coleta Metadados
                    data_post = "N/A"
                    try:
                        time_tag = li.find_element(By.TAG_NAME, "time")
                        data_post = time_tag.get_attribute("datetime")
                    except: pass

                    curtidas = "0"
                    if "curtida" in full_text:
                         for l in lines:
                             if "curtida" in l: curtidas = l
                             
                    signature = (autor, texto_final)
                    # Adiciona se o texto for válido e não for duplicata
                    if texto_final and signature not in seen_comments:
                        seen_comments.add(signature)
                        extracted_data.append({
                            "ID Post": post_id, 
                            "Autor": autor, 
                            "Data": data_post,
                            "Texto": texto_final,
                            "Curtidas": curtidas
                        })

                except Exception:
                    continue
                
        except Exception as e:
            print(f"⚠️ Erro ao processar post: {e}")
            
        return extracted_data

    def close(self): self.driver.quit()

def main():
    # Verifica se as credenciais foram carregadas
    if not INSTAGRAM_USERNAME or not INSTAGRAM_PASSWORD:
        print("❌ ERRO DE CONFIGURAÇÃO: O INSTAGRAM_USERNAME ou INSTAGRAM_PASSWORD não foi carregado do arquivo .env.")
        return

    scraper = InstagramCommentScraper(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
    
    # Cria/limpa o arquivo CSV com cabeçalho
    with open(CSV_FILENAME, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=["ID Post", "Autor", "Data", "Texto", "Curtidas"])
        writer.writeheader()

    try:
        scraper.login()
        
        # Mapeamento e Extração
        links = scraper.get_all_post_links(TARGET_PROFILE, target_count=300)
        
        for i, link in enumerate(links):
            print(f"--- Processando {i+1}/{len(links)} ---")
            new_data = scraper.extract_comments_from_post(link)
            
            # Salva os novos dados imediatamente no CSV (modo 'a' - append)
            if new_data:
                with open(CSV_FILENAME, 'a', newline='', encoding='utf-8-sig') as f:
                    writer = csv.DictWriter(f, fieldnames=["ID Post", "Autor", "Data", "Texto", "Curtidas"])
                    writer.writerows(new_data)
                print(f"💾 +{len(new_data)} linhas salvas no CSV.")
            
    finally:
        scraper.close()
        print(f"\n🏁 Processo de Web Scraping finalizado! Arquivo: {CSV_FILENAME}")

if __name__ == "__main__":
    main()

```
----------


## 🥈 Camada Silver: Tratamento e Unificação

A camada **Silver** é o coração da qualidade de dados deste projeto. Seu objetivo é transformar os dados brutos e fragmentados da camada Bronze em um dataset unificado, limpo e confiável, pronto para modelagem dimensional.

### 🛠️ O que o script faz (`etl_bronze_to_silver.py`)

O script de processamento executa uma série de transformações críticas para garantir a integridade dos dados:

1.  **Ingestão e Leitura Híbrida (Smart Encoding):**
    
    -   Resolve o problema de arquivos mistos (alguns em UTF-8, outros em Latin-1/Windows-1252).
        
    -   Utiliza uma lógica `try-except` para detectar automaticamente a codificação correta, eliminando caracteres corrompidos (_mojibake_) como `IPANGUAÃ‡U` -> `IPANGUAÇU`.
        
2.  **Limpeza Rigorosa (Data Quality):**
    
    -   **Remoção de Ruído:** Elimina linhas totalmente vazias ou cabeçalhos repetidos decorrentes da concatenação.
        
    -   **Validação de Completude:** Aplica uma regra de negócio que descarta registros onde campos chave (`Idade`, `Sexo` ou `Município`) estejam ausentes, garantindo que apenas dados utilizáveis avancem.
        
3.  **Tratamento Temporal:**
    
    -   Converte a coluna de texto `data_internacao` para objetos `datetime` reais.
        
    -   Remove datas inválidas (erros de digitação ou formatação).
        
    -   Ordena todo o dataset cronologicamente (do registro mais antigo ao mais recente).
        
4.  **Padronização de Saída:**
    
    -   Unifica todos os arquivos trimestrais em um único arquivo: `internacoes_unificadas.csv`.
        
    -   Salva no S3 com encoding **UTF-8-SIG** e separador **ponto e vírgula (;)**, facilitando a auditoria visual tanto em ferramentas de código (VS Code) quanto em planilhas (Excel/Power BI) sem erros de acentuação.

O script de processamento executa uma série de transformações críticas para garantir a integridade dos dados:

1.  **Ingestão e Leitura Híbrida (Smart Encoding):**
    
    -   Resolve o problema de arquivos mistos (alguns em UTF-8, outros em Latin-1/Windows-1252).
        
    -   Utiliza uma lógica `try-except` para detectar automaticamente a codificação correta, eliminando caracteres corrompidos (_mojibake_) como `IPANGUAÃ‡U` -> `IPANGUAÇU`.
        
2.  **Limpeza Rigorosa (Data Quality):**
    
    -   **Remoção de Ruído:** Elimina linhas totalmente vazias ou cabeçalhos repetidos decorrentes da concatenação.
        
    -   **Validação de Completude:** Aplica uma regra de negócio que descarta registros onde campos chave (`Idade`, `Sexo` ou `Município`) estejam ausentes, garantindo que apenas dados utilizáveis avancem.
        
3.  **Tratamento Temporal:**
    
    -   Converte a coluna de texto `data_internacao` para objetos `datetime` reais.
        
    -   Remove datas inválidas (erros de digitação ou formatação).
        
    -   Ordena todo o dataset cronologicamente (do registro mais antigo ao mais recente).
        
4.  **Padronização de Saída:**
    
    -   Unifica todos os arquivos trimestrais em um único arquivo: `internacoes_unificadas.csv`.
        
    -   Salva no S3 com encoding **UTF-8-SIG** e separador **ponto e vírgula (;)**, facilitando a auditoria visual tanto em ferramentas de código (VS Code) quanto em planilhas (Excel/Power BI) sem erros de acentuação.

    ### 🐍 Código da Etapa Silver (`etl_bronze_to_silver.py`)

Abaixo está o código completo utilizado para realizar a leitura, correção de _encoding_, limpeza de dados nulos e unificação dos arquivos CSV.

Python

```
import pandas as pd
import boto3
import os
from io import StringIO
from dotenv import load_dotenv
from pathlib import Path

# --- CARREGAMENTO DO .env ---
BASEDIR = Path(__file__).resolve().parent
dotenv_path = BASEDIR / '.env'
load_dotenv(dotenv_path=dotenv_path) 

# --- CONFIGURAÇÕES ---
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')

S3_BRONZE_PREFIX = 'bronze/'
S3_SILVER_KEY = 'silver/internacoes_unificadas.csv'

def etl_process_v3():
    print("🚀 [ETL V3] Iniciando: Leitura Híbrida + Limpeza + Ordenação...")
    
    if not BUCKET_NAME:
        print("❌ Erro: BUCKET_NAME não encontrado no .env")
        return

    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
    
    # 1. Listar arquivos
    try:
        response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=S3_BRONZE_PREFIX)
        arquivos = [obj['Key'] for obj in response.get('Contents', []) 
                    if obj['Key'].lower().endswith('.csv')
                    and 'comentarios' not in obj['Key'].lower()]
    except Exception as e:
        print(f"❌ Erro ao listar bucket: {e}")
        return

    print(f"📂 Encontrados {len(arquivos)} arquivos CSV.")
    
    lista_dfs = []

    # 2. Loop de Leitura e Limpeza (ARQUIVO POR ARQUIVO)
    for arquivo in arquivos:
        nome_arquivo = arquivo.split('/')[-1]
        try:
            obj = s3.get_object(Bucket=BUCKET_NAME, Key=arquivo)
            raw_data = obj['Body'].read()
            
            # --- CORREÇÃO DE ENCODING (INTELIGENTE) ---
            # Tenta UTF-8 primeiro (padrão web). Se falhar, usa Latin-1 (padrão legado).
            try:
                content = raw_data.decode('utf-8')
            except UnicodeDecodeError:
                content = raw_data.decode('latin1')
            
            # Tenta ler CSV
            try:
                df_temp = pd.read_csv(StringIO(content), sep=';')
                if len(df_temp.columns) < 2:
                    df_temp = pd.read_csv(StringIO(content), sep=',')
            except:
                 df_temp = pd.read_csv(StringIO(content), sep=',')

            # --- LIMPEZA DE DADOS (DENTRO DO LOOP) ---
            qtd_antes = len(df_temp)

            # 1. Remove linhas totalmente vazias
            df_temp.dropna(how='all', inplace=True)
            
            # 2. Limpeza Crítica: Se faltar Idade, Sexo ou Município, remove a linha
            # (Normaliza nomes para garantir que encontra as colunas mesmo se maiúscula/minúscula)
            col_map = {c: c.lower() for c in df_temp.columns}
            cols_criticas = []
            for original, lower in col_map.items():
                if 'idade' in lower or 'sexo' in lower or 'munic' in lower:
                    cols_criticas.append(original)
            
            if cols_criticas:
                df_temp.dropna(subset=cols_criticas, how='any', inplace=True)
            
            # 3. Filtra datas inválidas
            if 'data_internacao' in df_temp.columns:
                 df_temp = df_temp[df_temp['data_internacao'].notna()]

            qtd_depois = len(df_temp)
            removidas = qtd_antes - qtd_depois

            if qtd_depois > 0:
                print(f"   -> Lendo: {nome_arquivo}")
                if removidas > 0:
                    print(f"      🧹 Limpeza: {removidas} linhas incompletas removidas.")
                lista_dfs.append(df_temp)
            else:
                print(f"   ⚠️ ALERTA: Arquivo {nome_arquivo} ficou vazio após limpeza.")

        except Exception as e:
            print(f"   ❌ Erro em {nome_arquivo}: {e}")

    # 3. Consolidação Final
    if lista_dfs:
        df_final = pd.concat(lista_dfs, ignore_index=True)
        print(f"\n📊 Total Bruto: {len(df_final)} linhas.")

        # --- TRATAMENTO DE DATA E ORDENAÇÃO ---
        print("⏳ Convertendo e ordenando datas...")
        
        # Converte para datetime e remove erros
        df_final['data_internacao'] = pd.to_datetime(df_final['data_internacao'], dayfirst=True, errors='coerce')
        df_final = df_final.dropna(subset=['data_internacao'])
        
        # Ordena cronologicamente
        df_final.sort_values(by='data_internacao', ascending=True, inplace=True)
        
        print(f"✅ Ordenação concluída. Período: de {df_final['data_internacao'].min()} até {df_final['data_internacao'].max()}")

        # Salva no S3 (Silver)
        print("💾 Salvando na Silver...")
        csv_buffer = StringIO()
        # Salva como UTF-8-SIG (Universal para Excel) e separado por ponto e vírgula
        df_final.to_csv(csv_buffer, index=False, sep=';', encoding='utf-8-sig', date_format='%d/%m/%Y %H:%M')
        
        s3.put_object(Bucket=BUCKET_NAME, Key=S3_SILVER_KEY, Body=csv_buffer.getvalue())
        print(f"🏁 SUCESSO! Arquivo final salvo em: {S3_SILVER_KEY}")
    else:
        print("❌ Nenhum dado processado.")

if __name__ == "__main__":
    etl_process_v3()
```


## 💬 Camada Silver: Tratamento de Dados Não Estruturados (Comentários)

Nesta etapa, focamos na **Sanitização** e **Preservação de Contexto** dos comentários extraídos do Instagram. O objetivo é entregar um texto limpo, mas semanticamente rico, para a Camada Gold.

### 🛠️ O que foi feito (`etl_comentarios_silver.py`)

Diferente de abordagens tradicionais que removem caracteres especiais, nossa estratégia de engenharia priorizou a qualidade para modelos de IA:

1.  **Preservação de Emojis Nativos (UTF-8):**
    
    -   **Decisão:** Optamos por **não converter** os emojis em texto (`:cry:`) nem removê-los. Mantivemos os caracteres visuais originais (ex: 😢, 👏).
        
    -   **Motivo Técnico:** Algoritmos modernos de análise de sentimento (como o **pysentimiento**, que usaremos na Gold) possuem pesos específicos para os símbolos gráficos. Manter o emoji original maximiza a precisão da detecção de emoções intensas.
        
2.  **Filtro "Cirúrgico" de Scraping (Gatekeeper):**
    
    -   Implementamos regras de **Regex (Expressões Regulares)** para identificar e descartar artefatos de coleta que sujavam os dados:
        
        -   **Datas Soltas:** Remove linhas que contêm apenas metadados de tempo (ex: _"27 de novembro de 2024"_), diferenciando-as de comentários válidos que citam datas.
            
        -   **Interface:** Remove botões capturados como texto ("Seguir", "Responder", "Ver tradução").
            
        -   **Lixo Numérico:** Elimina linhas compostas apenas por números soltos.
            
3.  **Controle de Qualidade:**
    
    -   **Integridade Temporal:** Registros com data de publicação nula ou inválida são descartados imediatamente (`dropna`).
        
    -   **Normalização:** Conversão de "29 curtidas" para inteiros (`29`) e padronização de datas para `YYYY-MM-DD`.
        

### 🐍 Código da Etapa Silver - Comentários (V5)

Python

```
import pandas as pd
import boto3
import os
import re
from io import StringIO
from dotenv import load_dotenv
from pathlib import Path

# --- CONFIGURAÇÃO ---
BASEDIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASEDIR / '.env')

AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')

S3_INPUT_KEY = 'bronze/comentarios_huol_completo_223posts.csv'
S3_OUTPUT_KEY = 'silver/comentarios_tratados.csv'

# --- FUNÇÕES DE LIMPEZA ---

def limpar_texto_manter_emoji(texto):
    """
    Limpa formatação e links, mas MANTÉM os emojis originais (😢) para o VADER.
    """
    if not isinstance(texto, str):
        return ""
    
    # Remove URLs
    texto_sem_link = re.sub(r'http\S+', '', texto)
    
    # Remove quebras de linha e espaços duplos
    return re.sub(r'\s+', ' ', texto_sem_link).strip()

def extrair_numero_curtidas(valor):
    """Extrai apenas o número inteiro."""
    numeros = re.findall(r'\d+', str(valor))
    return int(numeros[0]) if numeros else 0

def filtrar_lixo_scraping(df):
    """
    Remove artefatos de coleta (botões, contadores e datas soltas no texto).
    """
    qtd_inicial = len(df)
    
    # 1. Blacklist de Interface
    lixo_interface = [
        'Seguir', 'Responder', 'Ver tradução', 
        'Ocultar', 'Ver todas as respostas', 'Ver respostas'
    ]
    df = df[~df['texto_limpo'].isin(lixo_interface)]
    df = df[~df['texto_limpo'].str.contains('Ver todas as', case=False)]
    
    # 2. Lixo Numérico
    df = df[~df['texto_limpo'].str.match(r'^\d+$')]
    
    # 3. Lixo de Datas soltas
    # Regex rigoroso para pegar linhas que são APENAS datas
    padrao_data = r'^[\d\s]*\d{1,2}\s+de\s+[a-zA-Zç]+(\s+de\s+\d{4})?.*$'
    
    mask_eh_data = df['texto_limpo'].str.match(padrao_data, case=False)
    mask_eh_curto = df['texto_limpo'].str.len() < 40 # Só deleta se for curto (sem contexto)
    
    df = df[~(mask_eh_data & mask_eh_curto)]
    
    removidos = qtd_inicial - len(df)
    if removidos > 0:
        print(f"      🧹 Faxina de Scraping: {removidos} linhas removidas.")
    
    return df

def etl_comentarios():
    print("🚀 [ETL Comentários V5] Iniciando (Emojis Nativos + Filtro Data)...")
    
    if not BUCKET_NAME:
        print("❌ Erro: BUCKET_NAME não encontrado.")
        return

    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
    
    try:
        print(f"📥 Baixando Bronze: {S3_INPUT_KEY}")
        obj = s3.get_object(Bucket=BUCKET_NAME, Key=S3_INPUT_KEY)
        df = pd.read_csv(obj['Body'], encoding='utf-8')
    except Exception as e:
        print(f"❌ Erro ao ler arquivo: {e}")
        return

    print("⚙️ Aplicando regras de limpeza...")
    
    # A. Limpeza de Texto (Mantendo Emoji)
    df['texto_limpo'] = df['Texto'].apply(limpar_texto_manter_emoji)
    
    # B. Filtro de Lixo de Scraping (Datas, botões)
    df = filtrar_lixo_scraping(df)
    
    # C. Dedup
    df.drop_duplicates(subset=['texto_limpo', 'Autor'], inplace=True)
    
    # D. Tratamento de Data (Remove Vazios)
    df['data_publicacao'] = pd.to_datetime(df['Data'], errors='coerce').dt.date
    df.dropna(subset=['data_publicacao'], inplace=True)
    
    # E. Métricas
    df['qtd_curtidas'] = df['Curtidas'].apply(extrair_numero_curtidas)
    
    # F. Seleção Final
    df_final = df[['data_publicacao', 'texto_limpo', 'qtd_curtidas', 'ID Post']]
    df_final = df_final[df_final['texto_limpo'] != '']
    
    print(f"📊 Total Final Limpo: {len(df_final)} linhas.")
    
    print(f"\n💾 Salvando Silver: {S3_OUTPUT_KEY}")
    csv_buffer = StringIO()
    df_final.to_csv(csv_buffer, index=False, sep=';', encoding='utf-8-sig')
    
    s3.put_object(Bucket=BUCKET_NAME, Key=S3_OUTPUT_KEY, Body=csv_buffer.getvalue())
    print("🏁 Sucesso!")

if __name__ == "__main__":
    etl_comentarios()

```
saida:

```
 Total Final Limpo: 567 linhas.

--- Amostra (Verifique os Emojis) ---
                                         texto_limpo
2  O HUOL é uma Instituição de referência, de déc...
3  👏🏼👏🏼 Huol é uma instituição de excelência. Ass...
4  Muita gratidão e respeito por essa instituição...
5    Muito orgulho de ser parte desta instituição! 🙌
6  Gostaria de saber porque que as varizes cirurg...

💾 Salvando Silver: silver/comentarios_tratados.csv
🏁 Sucesso!
```


## 🥇 Camada Gold: Modelagem e Inteligência Artificial

A camada **Gold** é o ponto culminante do Data Lake, onde os dados tratados são refinados para responder às perguntas de negócio. Nesta etapa, implementamos duas frentes de engenharia distintas: **Modelagem Dimensional** (para dados estruturados) e **Deep Learning** (para dados não estruturados).

### 1. Modelagem Dimensional (Star Schema)

Para viabilizar a análise performática no Power BI, transformamos o dataset plano de internações em um modelo relacional otimizado (**Star Schema**) utilizando o motor analítico **DuckDB**.

-   **Arquitetura:** Separação entre Fato (métricas) e Dimensões (contexto).
    
-   **Tabelas Geradas:**
    
    -   `dim_calendario`: Suporta análise temporal (Ano, Mês, Semestre).
        
    -   `dim_municipio`: Catálogo único de locais.
        
    -   `dim_especialidade`: Catálogo de especialidades médicas.
        
    -   `fato_internacoes`: Tabela central contendo as chaves estrangeiras (FKs) e métricas.
        
-   **Tecnologia:** DuckDB executando SQL em memória e exportando para formato **Parquet** (colunar), garantindo alta compressão e velocidade.

![Modelagem Dimensional (Star Schema](evidencias/005.jpg)
    

### 2. Análise de Sentimento (State-of-the-Art NLP)

Para classificar a percepção pública nos comentários do Instagram, abandonamos abordagens baseadas em léxicos simples (como VADER) e implementamos um modelo de **Deep Learning** baseado em Transformers (BERT).

-   **Modelo Utilizado:** `bertweet-pt-sentiment` (via biblioteca `pysentimiento`).
    
-   **Por que essa escolha?**
    
    -   **Nativo em Português:** Treinado em milhões de tweets brasileiros, entende gírias, ironia e erros gramaticais comuns.
        
    -   **Contexto Real:** Diferencia frases complexas (ex: _"Gostaria de saber por que as varizes estão suspensas"_ foi corretamente classificado como **Negativo** com 97% de confiança).
        
    -   **Suporte a Emojis:** Interpreta nativamente símbolos como 👏👏👏 (Positivo) e 🖤 (Luto/Negativo) sem necessidade de tradução ou conversão.
        

----------

### 🐍 Código: Modelagem Star Schema (`gold_star_schema.py`)

Python

```
import duckdb
import boto3
import os
import pandas as pd
from io import BytesIO
from dotenv import load_dotenv
from pathlib import Path

# --- CONFIGURAÇÃO ---
BASEDIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASEDIR / '.env')

AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')

S3_SILVER_KEY = 'silver/internacoes_unificadas.csv'
S3_GOLD_PREFIX = 'gold/'

def processar_gold_star_schema():
    print("🚀 [GOLD] Iniciando modelagem Dimensional (Star Schema)...")
    
    if not BUCKET_NAME:
        print("❌ Erro: BUCKET_NAME não encontrado.")
        return
    
    # 1. Baixar o CSV da Silver
    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
    
    try:
        print("📥 Baixando dados da Silver (Tabelão)...")
        obj = s3.get_object(Bucket=BUCKET_NAME, Key=S3_SILVER_KEY)
        # Lê com Pandas
        df_silver = pd.read_csv(obj['Body'], sep=';', encoding='utf-8')
        
        # --- CORREÇÃO DE CABEÇALHO ---
        # Renomeia 'município' para 'municipio' para facilitar o SQL
        df_silver.rename(columns={'município': 'municipio'}, inplace=True)
        
        # Garante que a data seja data mesmo
        df_silver['data_internacao'] = pd.to_datetime(df_silver['data_internacao'], dayfirst=True)
        
    except Exception as e:
        print(f"❌ Erro ao ler a Silver: {e}")
        return
    
    # 2. Iniciar DuckDB
    print("🦆 Iniciando motor SQL (DuckDB)...")
    con = duckdb.connect(database=':memory:')
    con.register('tb_silver', df_silver)
    
    # ---------------------------------------------------------
    # 3. CRIAR DIMENSÕES (SQL)
    # ---------------------------------------------------------
    
    print("🔨 [1/4] Criando Dimensão: Especialidade...")
    con.execute("""
        CREATE TABLE dim_especialidade AS
        SELECT 
            row_number() OVER (ORDER BY especialidade) AS id_especialidade,
            especialidade AS nome_especialidade
        FROM (SELECT DISTINCT especialidade FROM tb_silver WHERE especialidade IS NOT NULL)
    """)
    
    print("🔨 [2/4] Criando Dimensão: Município...")
    # Agora usamos 'municipio' sem acento
    con.execute("""
        CREATE TABLE dim_municipio AS
        SELECT 
            row_number() OVER (ORDER BY municipio) AS id_municipio,
            municipio AS nome_municipio
        FROM (SELECT DISTINCT municipio FROM tb_silver WHERE municipio IS NOT NULL)
    """)
    
    print("🔨 [3/4] Criando Dimensão: Calendário...")
    con.execute("""
        CREATE TABLE dim_calendario AS
        SELECT DISTINCT
            data_internacao AS id_calendario,
            YEAR(data_internacao) AS ano,
            MONTH(data_internacao) AS mes,
            DAY(data_internacao) AS dia,
            CASE 
                WHEN MONTH(data_internacao) <= 6 THEN 1 
                ELSE 2 
            END AS semestre
        FROM tb_silver
        WHERE data_internacao IS NOT NULL
        ORDER BY 1
    """)

    # ---------------------------------------------------------
    # 4. CRIAR FATO
    # ---------------------------------------------------------
    print("🔨 [4/4] Criando Tabela Fato: Internações...")
    con.execute("""
        CREATE TABLE fato_internacoes AS
        SELECT 
            s.data_internacao AS id_calendario,
            m.id_municipio,
            e.id_especialidade,
            s.idade,
            s.sexo,
            1 AS qtd_internacao
        FROM tb_silver s
        LEFT JOIN dim_municipio m ON s.municipio = m.nome_municipio
        LEFT JOIN dim_especialidade e ON s.especialidade = e.nome_especialidade
    """)
    
    # ---------------------------------------------------------
    # 5. SALVAR NO S3
    # ---------------------------------------------------------
    print("💾 Salvando tabelas na camada Gold (Parquet)...")
    
    tabelas = ['dim_especialidade', 'dim_municipio', 'dim_calendario', 'fato_internacoes']
    
    for tabela in tabelas:
        df_export = con.table(tabela).df()
        
        parquet_buffer = BytesIO()
        df_export.to_parquet(parquet_buffer, index=False)
        
        key = f"{S3_GOLD_PREFIX}{tabela}.parquet"
        s3.put_object(Bucket=BUCKET_NAME, Key=key, Body=parquet_buffer.getvalue())
        print(f"   ✅ {tabela} salva em: {key}")

    print("🏁 Sucesso! Data Warehouse criado.")

if __name__ == "__main__":
    processar_gold_star_schema()

```

### 🐍 Código: Análise de Sentimento com BERT (`analise_sentimento_gold.py`)

Python

```
import pandas as pd
import boto3
import os
from io import StringIO
from dotenv import load_dotenv
from pathlib import Path
from pysentimiento import create_analyzer

# --- CONFIGURAÇÃO ---
BASEDIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASEDIR / '.env')

AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')

S3_INPUT_KEY = 'silver/comentarios_tratados.csv'
S3_OUTPUT_KEY = 'gold/comentarios_sentimento_bert.csv'

def processar_com_bert():
    print("🚀 [GOLD] Iniciando Análise com BERT (Pysentimiento)...")
    
    # 1. Carrega o Modelo (BERTweet-PT)
    print("🧠 Carregando modelo 'bertweet-pt-sentiment'...")
    analyzer = create_analyzer(task="sentiment", lang="pt")

    # 2. Conecta no S3
    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
    print("📥 Baixando dados da Silver...")
    obj = s3.get_object(Bucket=BUCKET_NAME, Key=S3_INPUT_KEY)
    df = pd.read_csv(obj['Body'], sep=';', encoding='utf-8')

    # 3. Processamento
    print("⚙️ Analisando sentimentos (Deep Learning)...")
    
    sentimentos = []
    scores = []
    
    total = len(df)
    for i, row in df.iterrows():
        texto = row['texto_limpo']
        
        # O modelo processa direto o texto em PT com emojis
        resultado = analyzer.predict(texto)
        
        # O resultado vem como "POS", "NEG", "NEU" -> Mapeamos para PT
        mapa = {'POS': 'Positivo', 'NEG': 'Negativo', 'NEU': 'Neutro'}
        sentimentos.append(mapa[resultado.output])
        
        # Probabilidade da classe escolhida
        probabilidade = resultado.probas[resultado.output]
        
        # Ajuste de sinal para visualização (-1 a 1)
        if resultado.output == 'NEG':
            scores.append(probabilidade * -1)
        elif resultado.output == 'NEU':
            scores.append(0.0)
        else:
            scores.append(probabilidade)

        if i % 50 == 0:
            print(f"   ... Processado {i}/{total}")

    df['sentimento'] = sentimentos
    df['score_sentimento'] = scores
    
    # 4. Salvar
    print(f"\n💾 Salvando em: {S3_OUTPUT_KEY}")
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False, sep=';', encoding='utf-8-sig')
    s3.put_object(Bucket=BUCKET_NAME, Key=S3_OUTPUT_KEY, Body=csv_buffer.getvalue())
    print("🏁 Sucesso!")

if __name__ == "__main__":
    processar_com_bert()
```

Saida
```
--- Amostra Final (BERT) ---
                                         texto_limpo sentimento  score_sentimento
0  O HUOL é uma Instituição de referência, de déc...     Neutro          0.000000
1  👏🏼👏🏼 Huol é uma instituição de excelência. Ass...   Positivo          0.830135
2  Muita gratidão e respeito por essa instituição...   Positivo          0.990246
3    Muito orgulho de ser parte desta instituição! 🙌   Positivo          0.988792
4  Gostaria de saber porque que as varizes cirurg...   Negativo         -0.972792
5  Parabéns a todos que fazem do HUOL, uma instit...   Positivo          0.976684
6  O HUOL é uma instituição centenária e de refer...     Neutro          0.000000
7                                                👏👏👏   Positivo          0.760595

📊 Resumo:
sentimento
Positivo    337
Neutro      127
Negativo    103
Name: count, dtype: int64

💾 Salvando em: gold/comentarios_sentimento_bert.csv
🏁 Sucesso!
```


## ☁️ Configuração do Data Warehouse Serverless (AWS)

Para profissionalizar o acesso aos dados e permitir consultas SQL diretas sobre o Data Lake, implementamos uma arquitetura _serverless_ utilizando **AWS Glue** e **AWS Athena**. Isso elimina a necessidade de carregar arquivos manualmente e cria uma camada de abstração robusta para o Power BI.

### 1. Catalogação de Dados (AWS Glue)

O **AWS Glue Crawler** foi utilizado para escanear automaticamente a camada Gold no S3, inferir o esquema dos arquivos (Parquet e CSV) e criar as tabelas no Data Catalog.

![AWS Glue Crawler](evidencias/006.jpg)

-   **Crawler Name:** `crawler_hospital_gold`
    
-   **Data Source:** `s3://datalake-sad-huol-weillon/gold/`
    
-   **Output Database:** `db_hospital_gold`
    
-   **IAM Role:** `AWSGlueServiceRole-hospital-acesso` (Configurada com permissão de leitura/escrita no bucket específico).
    
-   **Schedule:** _On Demand_ (Execução manual para otimização de custos).
    

> **Estratégia de Organização:** Para garantir a correta inferência dos formatos (Parquet vs CSV), os arquivos no S3 foram organizados em subpastas dedicadas (`gold/fato_internacoes/`, `gold/comentarios/`, etc.), respeitando a regra de "uma tabela por pasta" do Glue.

### 2. Motor de Consulta (AWS Athena)

O **AWS Athena** atua como a interface SQL para os dados armazenados no S3, permitindo queries interativas e servindo como backend para ferramentas de BI.

![AWS Athena](evidencias/007.jpg)

-   **Configuração Obrigatória:** Definição do _Query Result Location_ no S3 (`s3://.../athena-results/`) para armazenar os metadados das consultas.
    
-   **Validação:** Testes de consistência realizados via SQL (`SELECT * FROM ...`) para garantir que os dados de sentimento e métricas hospitalares estavam acessíveis e tipados corretamente.
    
    

### 3. Conectividade (ODBC & Power BI)

A integração final com o dashboard foi realizada através do **Driver ODBC Amazon Athena**, proporcionando uma conexão segura e performática.

-   **Driver:** Simba Athena ODBC Driver (64-bit).
    
-   **Autenticação:** IAM Credentials (Access Key / Secret Key).
    
-   **DSN (Data Source Name):** `AthenaHospital`.
    
-   **Vantagem:** Permite que o Power BI utilize o modo **Import** ou **DirectQuery**, delegando o processamento pesado para a nuvem AWS em vez da máquina local.


## ⚙️ Integração Final: Cloud Data Warehouse (AWS Glue & Athena)

A etapa final do projeto garante que o Power BI possa consumir os dados modelados (Camada Gold) via SQL de forma performática e segura, sem depender de downloads locais.

### 1. Catalogação Serverless (AWS Glue)

O coração da integração é o **AWS Glue Data Catalog**. O Crawler (`crawler_hospital_gold`) foi configurado para escanear a estrutura organizada em S3 (pastas `gold/...`) e inferir automaticamente o esquema das tabelas (identificando campos como `int`, `string` e `timestamp` nos arquivos Parquet e CSV).

-   **Resultado:** Criação do banco de dados `db_hospital_gold` e das 5 tabelas (Dimensões, Fato e Sentimento), tornando o S3 consultável via SQL.
    

### 2. Motor de Consulta e Conexão (Athena & ODBC)

O AWS Athena foi configurado como o motor de consulta _serverless_.

![ODBC](evidencias/008.jpg)


-   **Query Engine:** Athena executa consultas SQL diretamente sobre os arquivos Parquet/CSV no S3, eliminando a necessidade de um servidor de banco de dados tradicional.
    
-   **Conectividade:** O Power BI Desktop foi conectado ao Athena utilizando o **Driver ODBC (Simba Athena)**, autenticado com as credenciais **IAM** do usuário.
    
-   **Resultado Final:** O dashboard no Power BI Desktop consome os dados em _streaming_ direto da nuvem, validando a arquitetura ponta a ponta.



## 📊 Visualização e Estratégia de Negócio (Dashboard)

Com a infraestrutura de dados validada e conectada, a etapa final consistiu na construção do painel de Business Intelligence. O objetivo central não foi apenas apresentar gráficos, mas transformar os dados processados em uma ferramenta de **Apoio à Decisão** (Decision Support System) para a diretoria do hospital.

### 🎯 Motivação e Foco Estratégico

A construção do dashboard foi estritamente guiada pelas perguntas de negócio estabelecidas no planejamento. Essa abordagem evita o desenvolvimento de métricas de vaidade e garante que cada visualização tenha um propósito claro: **subsidiar a viabilidade do credenciamento ao SUS**.

O painel foi estruturado para responder às seguintes **6 Perguntas Chave**:

1.  **Quais especialidades hospitalares concentram o maior número de internações?**
    
    -   _Impacto:_ Define o foco operacional e alocação de recursos.
        
2.  **Qual o perfil etário e de gênero dos pacientes internados?**
    
    -   _Impacto:_ Planejamento de leitos e especialidades (ex: Pediatria vs Geriatria).
        
3.  **Existem padrões por município (ex.: mais internações de residentes de Natal ou do interior)?**
    
    -   _Impacto:_ Entendimento da abrangência regional e logística.
        
4.  **Há sazonalidade nas internações (variação entre os meses de 2024 e 2025)?**
    
    -   _Impacto:_ Previsão de demanda e gestão de escalas de plantão.
        
5.  **O que as pessoas estão dizendo sobre o hospital?**
    
    -   _Impacto:_ Análise qualitativa da imagem institucional.
        
6.  **Quais percepções ou sentimentos predominam nos comentários do Instagram (positivos, negativos, neutros)?**
    
    -   _Impacto:_ KPI de reputação baseado em Inteligência Artificial.
        

### 📈 Implementação Visual (Solução)

Para responder a essas questões, o dashboard no Power BI foi dividido em três áreas estratégicas, utilizando os dados modelados no **Star Schema** e enriquecidos com **NLP**:

-   **Demanda e Geografia (Q1 e Q3):** Utilização de **Gráficos de Barras (Top N)** e **Treemaps** para evidenciar a alta concentração de atendimentos na Região Metropolitana e o ranking das especialidades mais buscadas.
    
-   **Perfil e Tendência (Q2 e Q4):** Implementação de uma **Pirâmide Etária** dinâmica e **Gráficos de Linha** temporais, permitindo a comparação de sazonalidade entre os anos fiscais.
![vq](evidencias/009.jpg)
    
-   **Inteligência Artificial (Q5 e Q6):** Aplicação dos resultados do modelo **BERT**, visualizados através de gráficos de **Rosca (Sentimento Predominante)** e tabelas detalhadas que expõem as principais críticas e elogios extraídos das redes sociais.

![v2](evidencias/010.jpg)

## ✨ Resultados e Insights

A arquitetura combina dados estruturados (governamentais) e não estruturados (redes sociais) em um **Data Lakehouse Serverless na AWS**, utilizando Inteligência Artificial para análise de reputação. 


### 📊 Visão Geral e Demanda

-   **Top 10 Especialidades:** Identificamos as áreas de maior pressão de demanda no SUS.
    
-   **Geografia:** O mapa de calor (Treemap) revelou que a demanda é altamente concentrada na Região Metropolitana (Natal e Parnamirim).
    

### 👥 Perfil do Paciente

-   **Pirâmide Etária:** Análise detalhada por gênero e faixas etárias de 10 anos.
    
-   **Sazonalidade:** Monitoramento mensal comparativo (2024 vs 2025) para prever picos de ocupação.
    

### 🧠 A Voz das Redes

-   **Sentimento:** O modelo BERT identificou uma predominância de **59% de Elogios**, validando a boa reputação do hospital.
    
-   **Qualitativo:** Tabela detalhada filtrando as "Top Críticas" para ação imediata da gestão.

Explore os resultados da análise no dashboard interativo a seguir.

👉 **[Acesse o Dashboard Interativo ](https://app.powerbi.com/view?r=eyJrIjoiNTVmYzIxNWQtYWNkYy00M2FmLWE1OTYtZDVhMTNiMzkxYmZjIiwidCI6IjE5OTA0MTBmLTJlYzctNDIyZi1iNmY3LTMzNDVkMGJjNTMzMyJ9)**

---
🎥 Vídeo Explicativo
Assista a uma apresentação completa do projeto, desde o ETL, implementação na nuvem, até o dashboard final:

👉 [Apresentação do Projeto no YouTube](xxxxxxxxxxxxxxxxxxx)

---
## 🚀 Tecnologias Utilizadas

-   **Cloud:** AWS S3, AWS Glue, AWS Athena.
    
-   **Linguagem:** Python 3.10+.
    
-   **Bibliotecas:** Pandas, Boto3, DuckDB, Pysentimiento (Transformers/BERT).
    
-   **Visualização:** Microsoft Power BI (Conector ODBC).
    

----------

## 👨‍💻 Autor

**Weillon Mota**

-   [LinkedIn](https://www.linkedin.com/in/weillonmota/)
    
-   [GitHub](https://github.com/weillonmota/projetos)
