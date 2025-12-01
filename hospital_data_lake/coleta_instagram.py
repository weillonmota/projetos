import csv
import time
from typing import List, Dict, Any, Set

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDriver

# --- CONFIGURAÇÕES ---
INSTAGRAM_USERNAME = "criativo.algoritmo"
INSTAGRAM_PASSWORD = "1965917aA@+"
TARGET_PROFILE = "https://www.instagram.com/huol_ufrn/"
CSV_FILENAME = "comentarios_huol_completo_223posts.csv"

class InstagramCommentScraper:
    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password
        self.driver = self._setup_driver()
        self.wait = WebDriverWait(self.driver, 20)

    def _setup_driver(self) -> WebDriver:
        firefox_options = Options()
        # firefox_options.add_argument("--headless") 
        service = Service(GeckoDriverManager().install())
        return webdriver.Firefox(service=service, options=firefox_options)

    def login(self) -> None:
        print("🔐 Fazendo Login...")
        self.driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(5)
        try:
            try: self.driver.find_element(By.XPATH, "//button[text()='Allow all cookies' or text()='Permitir todos os cookies']").click()
            except: pass
            
            self.wait.until(EC.element_to_be_clickable((By.NAME, "username"))).send_keys(self.username)
            time.sleep(1)
            self.driver.find_element(By.NAME, "password").send_keys(self.password)
            time.sleep(1)
            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "svg[aria-label='Home'], svg[aria-label='Página inicial']")))
            print("✅ Login realizado.")
            time.sleep(5)
        except Exception as e:
            print(f"❌ Falha no login: {e}")
            self.driver.quit(); exit()

    def get_all_post_links(self, profile_url: str, target_count: int = 250) -> List[str]:
        """
        Rola a página do perfil até encontrar todos os posts.
        """
        print(f"🔍 Mapeando posts do perfil: {profile_url}")
        self.driver.get(profile_url)
        time.sleep(5)
        
        post_links: Set[str] = set()
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        tentativas_sem_novos = 0
        
        print("   🔄 Rolando perfil para carregar posts antigos...")
        
        while len(post_links) < target_count:
            # Coleta links visíveis na tela atual
            anchors = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/p/')]")
            for anchor in anchors:
                href = anchor.get_attribute("href")
                if href: post_links.add(href)
            
            print(f"      -> {len(post_links)} posts encontrados...")
            
            # Rola para baixo
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3) 
            
            # Verifica se chegou ao fim
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                tentativas_sem_novos += 1
                if tentativas_sem_novos >= 3: 
                    print("   ✅ Fim da página de perfil.")
                    break
            else:
                tentativas_sem_novos = 0
                last_height = new_height
                
        lista_final = list(post_links)
        print(f"📌 Mapeamento concluído: {len(lista_final)} posts prontos para extração.")
        return lista_final

    def extract_comments_from_post(self, post_url: str) -> List[Dict[str, Any]]:
        print(f"\n📥 Acessando: {post_url}")
        self.driver.get(post_url)
        time.sleep(5) 
        
        extracted_data: List[Dict[str, Any]] = []
        seen_comments: Set[tuple] = set()
        
        try:
            post_id = post_url.split("/p/")[1].split("/")[0]
        except: post_id = "post_unk"

        try:
            # --- ANÁLISE DE VOLUME ---
            # Tenta encontrar a lista
            li_elements = self.driver.find_elements(By.XPATH, "//ul//li")
            if not li_elements:
                 li_elements = self.driver.find_elements(By.XPATH, "//div[@role='button']/../../..")
            
            count_inicial = len(li_elements)
            
            # Verifica se tem botão (+)
            tem_botao = False
            try:
                if self.driver.find_elements(By.XPATH, "//svg[descendant::circle and descendant::polyline]"):
                    tem_botao = True
            except: pass

            print(f"   -> Diagnóstico: {count_inicial} comentários visíveis.")

            # --- LÓGICA HÍBRIDA ---
            if count_inicial > 17 or tem_botao:
                # MODO MANUAL
                print("   🚨 POST GRANDE! Intervenção necessária.")
                print("   👉 Role a barra no Firefox até o fim.")
                input("   👉 Pressione ENTER aqui quando terminar de carregar tudo...")
                print("   🤖 Ok! Capturando dados...")
                
                # Atualiza a lista após rolagem manual
                li_elements = self.driver.find_elements(By.XPATH, "//ul//li")
                if not li_elements:
                     li_elements = self.driver.find_elements(By.XPATH, "//div[@role='button']/../../..")
            else:
                # MODO AUTOMÁTICO
                print("   ⚡ Post pequeno (<=17). Salvando automaticamente...")

            # --- EXTRAÇÃO ---
            print(f"   -> Processando {len(li_elements)} blocos...")

            for li in li_elements:
                try:
                    # Legenda (H1)
                    is_legenda = False
                    texto_final = ""
                    try:
                        h1 = li.find_element(By.TAG_NAME, "h1")
                        txt = h1.text.strip()
                        if len(txt) > 5: 
                            texto_final = txt
                            is_legenda = True
                    except: pass

                    full_text = li.text.strip()
                    lines = full_text.split('\n')
                    
                    autor = "Desconhecido"
                    if lines: autor = lines[0].strip()
                    
                    if not is_legenda:
                        if len(lines) < 2: continue
                        if autor in ["Ver insights", "Curtir", "Responder", "Ver tradução"]: continue

                        texto_parts = []
                        blacklist = ["Responder", "Reply", "Enviar", "Editado", "Ver insights", "Ocultar"]

                        for line in lines:
                            l = line.strip()
                            if l == autor: continue 
                            if "curtida" in l or "like" in l: continue
                            
                            is_time = False
                            if len(l) < 15 and any(c.isdigit() for c in l):
                                if "sem" in l or "d" in l or "h" in l: is_time = True
                            if is_time: continue
                            
                            if l in blacklist: continue
                            texto_parts.append(l)
                        
                        texto_final = " ".join(texto_parts).strip()

                    # Metadados
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
    scraper = InstagramCommentScraper(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
    # Cria o arquivo CSV com cabeçalho
    with open(CSV_FILENAME, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=["ID Post", "Autor", "Data", "Texto", "Curtidas"])
        writer.writeheader()

    try:
        scraper.login()
        
        # Passo 1: Mapear todos os 223 posts
        links = scraper.get_all_post_links(TARGET_PROFILE, target_count=300)
        
        # Passo 2: Processar um por um
        for i, link in enumerate(links):
            print(f"--- Processando {i+1}/{len(links)} ---")
            new_data = scraper.extract_comments_from_post(link)
            
            # Salva imediatamente (Append mode 'a')
            if new_data:
                with open(CSV_FILENAME, 'a', newline='', encoding='utf-8-sig') as f:
                    writer = csv.DictWriter(f, fieldnames=["ID Post", "Autor", "Data", "Texto", "Curtidas"])
                    writer.writerows(new_data)
                print(f"💾 +{len(new_data)} linhas salvas.")
            
    finally:
        scraper.close()
        print(f"\n🏁 Processo finalizado! Arquivo: {CSV_FILENAME}")

if __name__ == "__main__":
    main()