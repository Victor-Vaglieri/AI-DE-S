import os
import json
import re
import logging
from groq import Groq
from pydantic import ValidationError
from bs4 import BeautifulSoup
from app.settings import settings

logger = logging.getLogger("AI-DE-S.Processor")

class DataProcessor:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            logger.critical("Chave GROQ não encontrada nas variáveis de ambiente.")
            raise ValueError("chave api ausente")
        
        self.client = Groq(api_key=self.api_key, max_retries=5)

    def _clean_html_soup(self, html):
        objeto_sopa = BeautifulSoup(html, 'lxml')
        
        for tag_item in objeto_sopa(["script", "style", "svg", "noscript", "header", "footer", "nav", "iframe", "button"]):
            tag_item.decompose()

        for tag_atua in objeto_sopa.find_all(True):
            atrib_permi = ['href', 'src', 'class', 'id']
            atrib_atuais = dict(tag_atua.attrs)
            for nome_atrib in atrib_atuais:
                if nome_atrib not in atrib_permi:
                    del tag_atua[nome_atrib]

        texto_limpo = objeto_sopa.get_text(separator=' ', strip=True)
        limit_carac = settings.get("processor.max_html_chars", 18000)
        return texto_limpo[:limit_carac]

    def process(self, raw_html, schema):
        logger.info(f"Iniciando análise com schema: {schema.__name__}")

        texto_proce = self._clean_html_soup(raw_html)
        esquema_json = schema.model_json_schema()

        prompt_ia = f"""
        Extraia as informações deste texto de página web seguindo o schema JSON:
        {json.dumps(esquema_json, indent=2)}
        Responda APENAS o JSON válido.
        TEXTO: {texto_proce}
        """

        try:
            respon_ia = self.client.chat.completions.create(
                model=settings.get("llm.model", "llama-3.3-70b-versatile"),
                messages=[
                    {"role": "system", "content": "Você é um extrator de dados estruturados especialista em JSON."},
                    {"role": "user", "content": prompt_ia}
                ],
                response_format={"type": "json_object"},
                temperature=settings.get("llm.temperature", 0.1),
                max_tokens=settings.get("llm.max_tokens", 4096)
            )
            json_respo = json.loads(respon_ia.choices[0].message.content)
            return schema(**json_respo)
        except ValidationError as e:
            logger.error(f"Dados retornados pela IA não batem com o Schema: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro na comunicação ou processamento da IA: {e}")
            return None
