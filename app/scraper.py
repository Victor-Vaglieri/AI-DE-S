import random
import time
import logging
import threading
import subprocess
import re
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from app.settings import settings

logger = logging.getLogger("AI-DE-S.Scraper")

class WebScraper:
    _driver_lock = threading.Lock()
    _chrome_version = None

    def __init__(self):
        self.driver = None
    
    def _get_chrome_version(self):
        """Detecta e faz cache da versão majoritária do Chrome."""
        if WebScraper._chrome_version:
            return WebScraper._chrome_version
            
        import sys
        if sys.platform == 'win32':
            import winreg
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
                version, _ = winreg.QueryValueEx(key, "version")
                match = re.search(r'^(\d+)', version)
                if match:
                    version = int(match.group(1))
                    WebScraper._chrome_version = version
                    logger.info(f"Versão do Chrome detectada: {version}")
                    return version
            except Exception as e:
                logger.debug(f"Erro ao detectar versão do Chrome no HKCU: {e}")
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Google Chrome")
                version, _ = winreg.QueryValueEx(key, "version")
                match = re.search(r'^(\d+)', version)
                if match:
                    version = int(match.group(1))
                    WebScraper._chrome_version = version
                    logger.info(f"Versão do Chrome detectada: {version}")
                    return version
            except Exception as e:
                logger.debug(f"Erro ao detectar versão do Chrome no HKLM: {e}")

        try:
            for cmd in ['google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser']:
                try:
                    output = subprocess.check_output([cmd, '--version']).decode('utf-8')
                    match = re.search(r'Google Chrome (\d+)', output) or re.search(r'Chromium (\d+)', output)
                    if match:
                        version = int(match.group(1))
                        WebScraper._chrome_version = version
                        logger.info(f"Versão do Chrome detectada: {version}")
                        return version
                except Exception:
                    continue
        except Exception as e:
            logger.debug(f"Erro ao detectar versão do Chrome: {e}")
        return None

    def _get_options(self):
        opcoes_chrome = uc.ChromeOptions()
        if settings.get("scraper.headless", True):
            opcoes_chrome.add_argument("--headless=new") 
        opcoes_chrome.add_argument("--no-sandbox")
        opcoes_chrome.add_argument("--disable-dev-shm-usage")
        opcoes_chrome.add_argument("--disable-gpu")
        opcoes_chrome.add_argument("--window-size=1920,1080")
        opcoes_chrome.add_argument("--disable-extensions")
        opcoes_chrome.add_argument("--disable-setuid-sandbox")
        opcoes_chrome.add_argument("--disable-software-rasterizer")
        
        user_agent_str = settings.get('scraper.user_agent')
        opcoes_chrome.add_argument(f"user-agent={user_agent_str}")
        return opcoes_chrome

    def _start_driver(self):
        try:
            version_main = self._get_chrome_version()
            with self._driver_lock:
                logger.info("Iniciando instância do Chrome...")
                # Pequeno delay para evitar que múltiplas instâncias tentem patchear ao mesmo tempo
                time.sleep(random.uniform(1.0, 3.0))
                
                self.driver = uc.Chrome(
                    options=self._get_options(),
                    use_subprocess=True,
                    suppress_welcome=True,
                    version_main=version_main
                )
            
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            })
        except Exception as e:
            logger.error(f"Falha ao abrir navegador: {e}")
            if self.driver:
                try: self.driver.quit()
                except: pass
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
