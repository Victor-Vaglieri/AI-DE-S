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
        opcs = uc.ChromeOptions()
        if settings.get("scraper.headless", True):
            opcs.add_argument("--headless=new") 
        opcs.add_argument("--no-sandbox")
        opcs.add_argument("--disable-dev-shm-usage")
        opcs.add_argument("--disable-gpu")
        opcs.add_argument("--window-size=1920,1080")
        
        user_agent = settings.get('scraper.user_agent')
        opcs.add_argument(f"user-agent={user_agent}")
        return opcs

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
        alt_at = self.driver.execute_script("return document.body.scrollHeight")
        prof_scroll = settings.get("scraper.scroll_depth", 6)
        
        for i in range(1, prof_scroll): 
            scroll_pt = random.randint(400, 700)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_pt});")
            time.sleep(random.uniform(1.5, 3.0))
            alt_nov = self.driver.execute_script("return document.body.scrollHeight")
            if alt_nov == alt_at and i > 2: break
            alt_at = alt_nov

    def _remove_modals(self):
        scripts_limp = [
            "document.querySelectorAll('[class*=\"modal\"], [class*=\"overlay\"], [id*=\"modal\"]').forEach(el => el.remove());",
            "document.body.style.overflow = 'auto';",
            "document.querySelectorAll('button[class*=\"Close\"]').forEach(btn => btn.click());"
        ]
        for scpt in scripts_limp:
            try:
                self.driver.execute_script(scpt)
            except Exception:
                pass

    def fetch_content(self, url):
        lim_tent = settings.get("scraper.max_retries", 3)
        atraso_tent = settings.get("scraper.retry_delay", 5)

        for tent in range(1, lim_tent + 1):
            try:
                if tent > 1:
                    logger.info(f"Retentativa {tent}/{lim_tent}: {url}")
                    time.sleep(atraso_tent * tent)

                if not self.driver or not self.driver.service.is_connectable():
                    self._start_driver()
                
                if not self.driver: continue

                self.driver.get(url)
                
                elem_alv = settings.get("scraper.smart_wait_element", "body")
                WebDriverWait(self.driver, 25).until(EC.presence_of_element_located((By.TAG_NAME, elem_alv)))
                
                esp_min = settings.get("scraper.wait_time_min", 5)
                esp_max = settings.get("scraper.wait_time_max", 8)
                time.sleep(random.uniform(esp_min, esp_max))
                
                self._remove_modals()
                
                eh_glassdoor = "glassdoor" in url.lower()
                alt_at = self.driver.execute_script("return document.body.scrollHeight")
                prof_scroll = settings.get("scraper.scroll_depth", 6)
                
                for i in range(1, prof_scroll):
                    scroll_pt = random.randint(500, 900)
                    self.driver.execute_script(f"window.scrollBy(0, {scroll_pt});")
                    time.sleep(random.uniform(2, 4))
                    if eh_glassdoor: self._remove_modals()
                    alt_nov = self.driver.execute_script("return document.body.scrollHeight")
                    if alt_nov == alt_at and i > 3: break
                    alt_at = alt_nov
                
                return self.driver.page_source
            
            except Exception as e:
                logger.warning(f"Erro na tentativa {tent} para {url}: {e}")
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
