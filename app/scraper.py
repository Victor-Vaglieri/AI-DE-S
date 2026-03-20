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
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--window-size=1920,1080")
        self.options.binary_location = "/usr/bin/google-chrome"
        
        self.driver = None

    def _start_driver(self):
        try:
            self.driver = uc.Chrome(
                options=self.options,
                driver_executable_path="/usr/bin/chromedriver",
                version_main=120)
        except Exception as e:
            print(f"Erro ao iniciar driver: {e}")

    def fetch_content(self, url):
        try:
            if not self.driver:
                self._start_driver()
            
            self.driver.get(url)
            wait = WebDriverWait(self.driver, 100)
            
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            for _ in range(3):
                self.driver.execute_script("window.scrollBy(0, 800);")
                time.sleep(2)

            body_element = self.driver.find_element(By.TAG_NAME, "body")
            
            return body_element.text
        
        except Exception as e:
            print(f"Erro na extração: {e}")
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