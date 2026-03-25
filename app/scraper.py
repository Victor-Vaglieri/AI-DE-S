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
        options.add_argument("--headless") 
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        return options

    def _start_driver(self):
        try:
            self.driver = uc.Chrome(options=self._get_options())
        except Exception as e:
            print(f"Erro ao iniciar driver: {e}")

    def fetch_content(self, url):
        try:
            if not self.driver:
                self._start_driver()
            
            self.driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {
                'headers': {
                    'Referer': 'https://www.google.com/',
                    'Accept-Language': 'pt-BR,pt;q=0.9'
                }
            })
            self.driver.get(url)
            time.sleep(random.uniform(6, 10))
            
            wait = WebDriverWait(self.driver, 100)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            self.driver.execute_script("window.scrollTo(0, 50);")
            time.sleep(2)
            for _ in range(3):
                self.driver.execute_script("window.scrollBy(0, 800);")
                time.sleep(2)
            body_element = self.driver.find_element(By.TAG_NAME, "body")
            return body_element.text
        
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
                