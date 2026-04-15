import pytest
from unittest.mock import MagicMock, patch
from app.scraper import WebScraper
import undetected_chromedriver as uc

def test_scraper_options():
    scraper = WebScraper()
    options = scraper._get_options()
    
    arguments = options.arguments
    assert "--no-sandbox" in arguments
    assert "--disable-dev-shm-usage" in arguments
    assert "--headless=new" in arguments
    assert "--disable-gpu" in arguments
    
    assert isinstance(options, uc.ChromeOptions)

def test_scraper_start_driver_failure(mocker):
    mocker.patch("undetected_chromedriver.Chrome", side_effect=Exception("Failed to start"))
    
    scraper = WebScraper()
    scraper._start_driver()
    
    assert scraper.driver is None

@patch("undetected_chromedriver.Chrome")
def test_scraper_start_driver_success(mock_chrome):
    mock_instance = MagicMock()
    mock_chrome.return_value = mock_instance
    scraper = WebScraper()
    scraper._start_driver()
    assert scraper.driver is not None
    mock_instance.execute_cdp_cmd.assert_called_once_with(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"}
    )
