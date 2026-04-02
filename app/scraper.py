import random
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class WebScraper:
    def __init__(self):
        self.driver = None
    
    def _get_options(self):
        options = uc.ChromeOptions()
        # Modo headless moderno que é menos detectado
        options.add_argument("--headless=new") 
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        return options

    def _start_driver(self):
        try:
            self.driver = uc.Chrome(options=self._get_options(), version_main=146)
            # Bypass adicional: Remove o flag de automação via CDP
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            })
        except Exception as e:
            print(f"  [ERROR] Falha ao iniciar driver: {e}")
            self.driver = None

    def _human_scroll(self):
        """Scroll incremental para simular humano e ativar lazy-loading."""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        for i in range(1, 5):  # Faz até 4 scrolls graduais
            scroll_by = random.randint(400, 700)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_by});")
            time.sleep(random.uniform(1.5, 3.0))
            
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height and i > 2: break
            last_height = new_height

    def _remove_modals(self):
        """Remove modais de login/assinatura que bloqueiam a visão (comum no Glassdoor)."""
        scripts = [
            "document.querySelectorAll('[class*=\"modal\"], [class*=\"overlay\"], [id*=\"modal\"]').forEach(el => el.remove());",
            "document.body.style.overflow = 'auto';",
            "document.querySelectorAll('button[class*=\"Close\"]').forEach(btn => btn.click());"
        ]
        for script in scripts:
            try:
                self.driver.execute_script(script)
            except:
                pass

    def fetch_content(self, url):
        try:
            if not self.driver or not self.driver.service.is_connectable():
                self._start_driver()
            
            if not self.driver: return None

            self.driver.get(url)
            WebDriverWait(self.driver, 25).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Pausa para o Glassdoor/LinkedIn processar o anti-bot inicial
            time.sleep(random.uniform(6, 10))
            
            # Limpa modais que podem ter aparecido
            self._remove_modals()
            
            # Tenta encontrar o container de vagas específico se for Glassdoor
            is_glassdoor = "glassdoor" in url.lower()
            
            # Executa o scroll incremental
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            for i in range(1, 6):
                scroll_by = random.randint(500, 900)
                self.driver.execute_script(f"window.scrollBy(0, {scroll_by});")
                time.sleep(random.uniform(2, 4))
                
                # No Glassdoor, modais reaparecem durante o scroll
                if is_glassdoor: self._remove_modals()
                
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height and i > 3: break
                last_height = new_height

            # Força o carregamento de imagens/cards finais
            time.sleep(3)

            return self.driver.page_source
        
        except Exception as e:
            print(f"  [ERROR] Falha na extração de {url}: {e}")
            return None
        
    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            finally:
                self.driver = None
