import pytest
from unittest.mock import MagicMock
from app.processor import DataProcessor
from app.schemas.jobs import JobList
import os

@pytest.fixture
def mock_processor(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test_key")
    with pytest.MonkeyPatch().context() as m:
        m.setattr("app.processor.Groq", MagicMock())
        processor = DataProcessor()
    return processor

def test_clean_html(mock_processor):
    html = """
    <html>
        <head><script>console.log('test')</script></head>
        <body>
            <header>Logo</header>
            <nav>Links</nav>
            <main>
                <h1 class="title">Vaga de Python</h1>
                <p>Descricao aqui</p>
                <svg>...</svg>
                <button>Apply</button>
            </main>
            <footer>Contact</footer>
        </body>
    </html>
    """
    cleaned = mock_processor._clean_html_soup(html)

    assert "Logo" not in cleaned
    assert "Links" not in cleaned
    assert "Contact" not in cleaned
    assert "Vaga de Python" in cleaned
    assert "Descricao aqui" in cleaned

    assert "<button" not in cleaned
    assert "Vaga de Python" in cleaned
    assert "Descricao aqui" in cleaned

def test_processor_invalid_json(mock_processor, mocker):
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Not a JSON"
    mock_processor.client.chat.completions.create.return_value = mock_response
    
    result = mock_processor.process("<html>test</html>", JobList)
    assert result is None

def test_processor_success(mock_processor, mocker):
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"vagas": [{"titulo": "Python Developer", "empresa": "Tech Corp"}]}'
    mock_processor.client.chat.completions.create.return_value = mock_response
    
    result = mock_processor.process("<html>test</html>", JobList)
    assert isinstance(result, JobList)
    assert len(result.vagas) == 1
    assert result.vagas[0].titulo == "Python Developer"
    assert result.vagas[0].empresa == "Tech Corp"
