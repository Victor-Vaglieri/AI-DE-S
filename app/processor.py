import os
import json
import re
import logging
from groq import Groq
from pydantic import ValidationError

logger = logging.getLogger("AI-DE-S.Processor")

class DataProcessor:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            logger.critical("Chave GROQ nao encontrada.")
            raise ValueError("chave nao encontrada")
        
        self.client = Groq(api_key=self.api_key)

    def _clean_html(self, html):
        html = re.sub(r'<(script|style|svg|noscript|header|footer|nav|iframe|button|path|form|input|label|meta|link).*?>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
        
        def clean_attrs(match):
            tag_content = match.group(0)
            preserved = re.findall(r'\s(href|src|data-[a-z0-9-]+)="[^"]*"', tag_content, re.IGNORECASE)
            tag_name = re.search(r'<([a-z0-9]+)', tag_content, re.IGNORECASE).group(1)
            attrs_str = " ".join([f'{k}="..."' for k in preserved])
            return f'<{tag_name} {attrs_str}>'

        html = re.sub(r'<[a-z0-9]+[^>]*>', clean_attrs, html, flags=re.IGNORECASE)
        html = re.sub(r'\s+', ' ', html).strip()
        return html

    def process(self, raw_html, schema):
        logger.info(f"Analisando com {schema.__name__}")

        clean_text = self._clean_html(raw_html)
        schema_json = schema.model_json_schema()
        input_text = clean_text[:20000]

        prompt = f"""
        Extraia as informações do HTML seguindo este schema:
        {json.dumps(schema_json, indent=2)}
        Responda APENAS o JSON.
        HTML: {input_text}
        """

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Assistente de extracao JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            json_response = json.loads(response.choices[0].message.content)
            return schema(**json_response)
        except ValidationError as e:
            logger.error(f"Erro de validacao: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro na IA: {e}")
            return None
