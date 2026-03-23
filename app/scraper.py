import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class WebScraper:
    def __init__(self):
        self.options = uc.ChromeOptions()
        self.options.add_argument("--headless") 
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_argument("--disable-notifications")
        self.options.add_argument("--lang=pt-BR")
        self.options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        

        self.driver = None

    def _start_driver(self):
        try:
            self.driver = uc.Chrome(options=self.options)
        except Exception as e:
            print(f"Erro ao iniciar driver: {e}")

    def fetch_content(self, url):
        try:
            try:
                if not self.driver or not self.driver.current_window_handle:
                    self._start_driver()
            except:
                self._start_driver()
            
            self.driver.get(url)
            
            wait = WebDriverWait(self.driver, 100)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            for _ in range(3):
                self.driver.execute_script("window.scrollBy(0, 800);")
                time.sleep(2)

            body_element = self.driver.find_element(By.TAG_NAME, "body")
            text = body_element.text

            if len(text) < 500:
                print(f"AVISO: Conteúdo muito curto vindo de {url}. Pode ser bloqueio.")

            return text
        
        except Exception as e:
            print(f"Erro na extração de {url}: {e}")
            self.close()
            return None
        
    def close(self):
        if self.driver:
            try:
                self.driver.close()
                self.driver.quit()
            except:
                pass
            finally:
                self.driver = None