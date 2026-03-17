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
        
        self.driver = None

    def _start_driver(self):
        try:
            self.driver = uc.Chrome(options=self.options)
        except Exception as e:
            print(e)

    def fetch_content(self, url):
        try:
            if not self.driver:
                self._start_driver()
            
            self.driver.get(url)

            wait = WebDriverWait(self.driver, 20)
            
            body_element = wait.until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            time.sleep(2) 
            
            return body_element.text
        
        except Exception as e:
            print(e)
            return None
        
    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None

if __name__ == "__main__":
    scraper = WebScraper()
    content = scraper.fetch_content("https://codevagas.dev/?level=junior&work_model=remote%2Chybrid%2Consite&date_filter=week")
    if content:
        print(f"\n{content[:500]}")
    scraper.close()