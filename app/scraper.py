import random
import time
import logging
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from app.settings import settings

logger = logging.getLogger("AI-DE-S.Scraper")

class WebScraper:
    def __init__(self):
        self.driver = None
    
    def _get_options(self):
        opcoes_chrome = uc.ChromeOptions()
        if settings.get("scraper.headless", True):
            opcoes_chrome.add_argument("--headless=new") 
        opcoes_chrome.add_argument("--no-sandbox")
        opcoes_chrome.add_argument("--disable-dev-shm-usage")
        opcoes_chrome.add_argument("--disable-gpu")
        opcoes_chrome.add_argument("--window-size=1920,1080")
        
        user_agent_str = settings.get('scraper.user_agent')
        opcoes_chrome.add_argument(f"user-agent={user_agent_str}")
        return opcoes_chrome

    def _start_driver(self):
        try:
            logger.info("Iniciando Chrome...")
            self.driver = uc.Chrome(options=self._get_options(), version_main=146)
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            })
        except Exception as e:
            logger.error(f"Falha ao abrir navegador: {e}")
            self.driver = None

    def _human_scroll(self):
        altura_atua = self.driver.execute_script("return document.body.scrollHeight")
        profun_scroll = settings.get("scraper.scroll_depth", 6)
        
        for i in range(1, profun_scroll): 
            scroll_pont = random.randint(400, 700)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_pont});")
            time.sleep(random.uniform(1.5, 3.0))
            altura_nova = self.driver.execute_script("return document.body.scrollHeight")
            if altura_nova == altura_atua and i > 2: break
            altura_atua = altura_nova

    def _remove_modals(self):
        script_limp = [
            "document.querySelectorAll('[class*=\"modal\"], [class*=\"overlay\"], [id*=\"modal\"]').forEach(el => el.remove());",
            "document.body.style.overflow = 'auto';",
            "document.querySelectorAll('button[class*=\"Close\"]').forEach(btn => btn.click());"
        ]
        for scrip_atua in script_limp:
            try:
                self.driver.execute_script(scrip_atua)
            except Exception:
                pass

    def fetch_content(self, url):
        limit_tentat = settings.get("scraper.max_retries", 3)
        atraso_tentat = settings.get("scraper.retry_delay", 5)

        for tenta_atua in range(1, limit_tentat + 1):
            try:
                if tenta_atua > 1:
                    logger.info(f"Retentativa {tenta_atua}/{limit_tentat}: {url}")
                    time.sleep(atraso_tentat * tenta_atua)

                if not self.driver or not self.driver.service.is_connectable():
                    self._start_driver()
                
                if not self.driver: continue

                self.driver.get(url)
                
                eleme_alvo = settings.get("scraper.smart_wait_element", "body")
                WebDriverWait(self.driver, 25).until(EC.presence_of_element_located((By.TAG_NAME, eleme_alvo)))
                
                espera_min = settings.get("scraper.wait_time_min", 5)
                espera_max = settings.get("scraper.wait_time_max", 8)
                time.sleep(random.uniform(espera_min, espera_max))
                
                self._remove_modals()
                
                eh_glassdoor = "glassdoor" in url.lower()
                altura_atua = self.driver.execute_script("return document.body.scrollHeight")
                profun_scroll = settings.get("scraper.scroll_depth", 6)
                
                for i in range(1, profun_scroll):
                    scroll_pont = random.randint(500, 900)
                    self.driver.execute_script(f"window.scrollBy(0, {scroll_pont});")
                    time.sleep(random.uniform(2, 4))
                    if eh_glassdoor: self._remove_modals()
                    altura_nova = self.driver.execute_script("return document.body.scrollHeight")
                    if altura_nova == altura_atua and i > 3: break
                    altura_atua = altura_nova
                
                return self.driver.page_source
            
            except Exception as e:
                logger.warning(f"Erro na tentativa {tenta_atua} para {url}: {e}")
                if self.driver:
                    try: self.driver.quit()
                    except: pass
                    self.driver = None
        
        logger.error(f"Esgotadas as tentativas para a URL: {url}")
        return None
        
    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            finally:
                self.driver = None
