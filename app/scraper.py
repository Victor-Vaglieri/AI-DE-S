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
            # Mantendo a versão 146 que você possui
            self.driver = uc.Chrome(options=self._get_options(), version_main=146)
        except Exception as e:
            print(f"  [ERROR] Falha ao iniciar driver: {e}")
            self.driver = None

    def fetch_content(self, url):
        try:
            if not self.driver:
                self._start_driver()
            
            if not self.driver: return None

            self.driver.get(url)
            # Espera o corpo da página carregar
            WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Tempo para o JavaScript do LinkedIn/Glassdoor rodar
            time.sleep(12)
            
            # Scroll para carregar elementos de lazy-loading
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(3)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
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
