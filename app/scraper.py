import asyncio
import logging
import random
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.settings import settings

logger = logging.getLogger("AI-DE-S.Scraper")

class WebScraper:
    _playwright = None
    _browser = None
    _lock = asyncio.Lock()

    @classmethod
    async def get_browser(cls):
        async with cls._lock:
            if not cls._playwright:
                logger.info("Iniciando Playwright e Chromium...")
                cls._playwright = await async_playwright().start()
                headless = settings.get("scraper.headless", True)
                cls._browser = await cls._playwright.chromium.launch(
                    headless=headless,
                    args=[
                        "--disable-gpu",
                        "--disable-dev-shm-usage",
                        "--no-sandbox"
                    ]
                )
        return cls._browser

    @classmethod
    async def close_browser(cls):
        async with cls._lock:
            if cls._browser:
                await cls._browser.close()
                cls._browser = None
            if cls._playwright:
                await cls._playwright.stop()
                cls._playwright = None

    @retry(
        stop=stop_after_attempt(settings.get("scraper.max_retries", 3)),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def fetch_content(self, url: str) -> str:
        browser = await self.get_browser()
        user_agent = settings.get("scraper.user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        context = await browser.new_context(
            user_agent=user_agent,
            viewport={"width": 1920, "height": 1080}
        )
        
        page = await context.new_page()
        
        await page.route(
            "**/*",
            lambda route: route.abort() if route.request.resource_type in ["image", "media", "font"] else route.continue_()
        )

        try:
            logger.debug(f"Navegando para {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            target_element = settings.get("scraper.smart_wait_element", "body")
            try:
                await page.wait_for_selector(target_element, timeout=15000)
            except PlaywrightTimeoutError:
                logger.warning(f"Timeout aguardando {target_element} em {url}. Continuando assim mesmo.")

            # scroll
            scroll_depth = settings.get("scraper.scroll_depth", 6)
            for _ in range(scroll_depth):
                scroll_amount = random.randint(400, 800)
                await page.evaluate(f"window.scrollBy(0, {scroll_amount});")
                await asyncio.sleep(random.uniform(0.5, 1.5))
            
            content = await page.content()
            return content
            
        except PlaywrightTimeoutError as pte:
            logger.error(f"Timeout total ao extrair {url}: {pte}")
            raise
        except Exception as e:
            logger.error(f"Erro ao extrair {url}: {str(e)}")
            raise
        finally:
            await context.close()
