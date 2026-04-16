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
        # Input/Global (English)
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            logger.critical("Chave GROQ não encontrada nas variáveis de ambiente.")
            raise ValueError("chave api ausente")
        
        self.client = Groq(api_key=self.api_key)

    def _clean_html_soup(self, html):
        sopa = BeautifulSoup(html, 'lxml')
        
        # Remover lixo
        for tg in sopa(["script", "style", "svg", "noscript", "header", "footer", "nav", "iframe", "button"]):
            tg.decompose()

        # Limpeza de atributos
        for tg in sopa.find_all(True):
            atrs_perm = ['href', 'src', 'class', 'id']
            atrs_atuais = dict(tg.attrs)
            for at in atrs_atuais:
                if at not in atrs_perm:
                    del tg[at]

        txt_limpo = sopa.get_text(separator=' ', strip=True)
        lim_carac = settings.get("processor.max_html_chars", 18000)
        return txt_limpo[:lim_carac]

    def process(self, raw_html, schema):
        logger.info(f"Iniciando análise com schema: {schema.__name__}")

        txt_proc = self._clean_html_soup(raw_html)
        esquema_json = schema.model_json_schema()

        prpt = f"""
        Extraia as informações deste texto de página web seguindo o schema JSON:
        {json.dumps(esquema_json, indent=2)}
        Responda APENAS o JSON válido.
        TEXTO: {txt_proc}
        """

        try:
            resp_ia = self.client.chat.completions.create(
                model=settings.get("llm.model", "llama-3.3-70b-versatile"),
                messages=[
                    {"role": "system", "content": "Você é um extrator de dados estruturados especialista em JSON."},
                    {"role": "user", "content": prpt}
                ],
                response_format={"type": "json_object"},
                temperature=settings.get("llm.temperature", 0.1),
                max_tokens=settings.get("llm.max_tokens", 4096)
            )
            json_resp = json.loads(resp_ia.choices[0].message.content)
            return schema(**json_resp)
        except ValidationError as e:
            logger.error(f"Dados retornados pela IA não batem com o Schema: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro na comunicação ou processamento da IA: {e}")
            return None
