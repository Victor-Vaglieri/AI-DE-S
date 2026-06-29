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
        soup = BeautifulSoup(html, 'lxml')
        
        for tag in soup(["script", "style", "svg", "noscript", "header", "footer", "nav", "iframe", "button", "aside", "form", "meta", "link"]):
            tag.decompose()

        main_content = None
        selectors = [
            'main', 'article', '#content', '#main', '.job-description', 
            '.post-content', '[role="main"]', '.description', '#job-details',
            '.show-more-less-html__markup', '.jobs-description'
        ]

        job_cards = soup.select('.job-search-card, .base-search-card, li.jobs-search-results__list-item, div[class*="job-card"]')
        
        if job_cards and len(job_cards) > 1:
            text_blocks = []
            for card in job_cards:
                text_blocks.append(card.get_text(separator=' ', strip=True))
            clean_text = "\n\n---\n\n".join(text_blocks)
        else:
            for selector in selectors:
                found = soup.select_one(selector)
                if found:
                    main_content = found
                    break
            
            target_soup = main_content if main_content else soup
            
            clean_text = md(str(target_soup), strip=['a', 'img', 'div', 'span', 'class', 'id', 'ul', 'li'], heading_style="ATX")
            
        clean_text = "\n".join([line.strip() for line in clean_text.splitlines() if line.strip()])
        
        char_limit = settings.get("processor.max_html_chars", 12000)
        return clean_text[:char_limit]

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=3, min=10, max=60),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def process(self, raw_html_or_text: str, schema: type[BaseModel]):
        logger.info(f"Iniciando análise com schema: {schema.__name__}")

        if "=== NOVA VAGA ===" in raw_html_or_text or not raw_html_or_text.strip().startswith("<"):
            processed_text = raw_html_or_text
        else:
            processed_text = self._clean_html_soup(raw_html_or_text)

        system_prompt = "Você é um extrator de dados estruturados especialista. Extraia as informações detalhadas do texto, prestando MUITA ATENÇÃO a Salário e Requisitos."
        if schema.__name__ == "JobList":
            system_prompt += " O texto pode conter múltiplas vagas separadas por '=== NOVA VAGA ==='. Extraia os detalhes de CADA UMA."

        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=settings.get("llm.model", "gemini-2.5-flash"),
                response_model=schema,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": processed_text}
                ],
                config=genai.types.GenerateContentConfig(
                    temperature=settings.get("llm.temperature", 0.1),
                    max_output_tokens=settings.get("llm.max_tokens", 4096)
                )
            )
            return response
            
        except Exception as e:
            logger.error(f"Erro na comunicação ou processamento da IA: {e}")
            raise
