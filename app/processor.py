import os
import logging
import asyncio
import instructor
from google import genai
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.settings import settings

logger = logging.getLogger("AI-DE-S.Processor")

class DataProcessor:
    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY")
        if not self.api_key:
            logger.critical("Chave LLM (LLM_API_KEY) não encontrada nas variáveis de ambiente.")
            raise ValueError("chave api ausente")
        
        self.client = instructor.from_genai(
            client=genai.Client(api_key=self.api_key),
            mode=instructor.Mode.GENAI_STRUCTURED_OUTPUTS
        )

    def _clean_html_soup(self, html: str) -> str:
        objeto_sopa = BeautifulSoup(html, 'lxml')
        
        for tag_item in objeto_sopa(["script", "style", "svg", "noscript", "header", "footer", "nav", "iframe", "button"]):
            tag_item.decompose()

        texto_limpo = md(str(objeto_sopa), strip=['a', 'img'], heading_style="ATX")
        texto_limpo = "\n".join([line.strip() for line in texto_limpo.splitlines() if line.strip()])
        
        limit_carac = settings.get("processor.max_html_chars", 18000)
        return texto_limpo[:limit_carac]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=20),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def process(self, raw_html: str, schema: type[BaseModel]):
        logger.info(f"Iniciando análise com schema: {schema.__name__}")

        texto_proce = self._clean_html_soup(raw_html)

        try:
            resposta = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=settings.get("llm.model", "gemini-2.5-flash"),
                response_model=schema,
                messages=[
                    {"role": "system", "content": "Você é um extrator de dados estruturados especialista. Extraia as informações do texto."},
                    {"role": "user", "content": texto_proce}
                ],
                config=genai.types.GenerateContentConfig(
                    temperature=settings.get("llm.temperature", 0.1),
                    max_output_tokens=settings.get("llm.max_tokens", 4096)
                )
            )
            return resposta
            
        except Exception as e:
            logger.error(f"Erro na comunicação ou processamento da IA: {e}")
            raise
