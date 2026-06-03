import pytest
from unittest.mock import AsyncMock, patch
from app.scraper import WebScraper

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.fixture
def mock_playwright():
    with patch("app.scraper.async_playwright") as mock_pw:
        mock_pw_context = AsyncMock()
        mock_browser = AsyncMock()
        mock_pw_context.start.return_value.chromium.launch.return_value = mock_browser
        mock_pw.return_value = mock_pw_context
        yield mock_pw_context

@pytest.mark.anyio
async def test_get_browser(mock_playwright):
    WebScraper._playwright = None
    WebScraper._browser = None
    
    browser = await WebScraper.get_browser()
    assert browser is not None
    mock_playwright.start.assert_called_once()

@pytest.mark.anyio
async def test_close_browser(mock_playwright):
    WebScraper._playwright = None
    WebScraper._browser = None
    
    await WebScraper.get_browser()
    await WebScraper.close_browser()
    
    assert WebScraper._browser is None
    assert WebScraper._playwright is None

@pytest.mark.anyio
async def test_fetch_content(mock_playwright):
    WebScraper._playwright = None
    WebScraper._browser = None
    
    scraper = WebScraper()
    
    mock_page = AsyncMock()
    mock_page.content.return_value = "<html>Test Content</html>"
    
    mock_context = AsyncMock()
    mock_context.new_page.return_value = mock_page
    
    mock_browser = AsyncMock()
    mock_browser.new_context.return_value = mock_context
    
    with patch.object(WebScraper, 'get_browser', return_value=mock_browser):
        content = await scraper.fetch_content("http://test.com")
        assert content == "<html>Test Content</html>"
        mock_page.goto.assert_called_once_with("http://test.com", wait_until="domcontentloaded", timeout=30000)
