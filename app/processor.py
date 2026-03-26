import os
import json
import re
from groq import Groq
from pydantic import ValidationError

class DataProcessor:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("chave não encontrada")
        
        self.client = Groq(api_key=self.api_key)

    def _clean_html(self, html):
        """Remoção máxima de ruído HTML para caber no limite de 12k tokens."""
        html = re.sub(r'<(script|style|svg|noscript|header|footer|nav|iframe|button|path|form|input).*?>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
        html = re.sub(r'(\s)([a-zA-Z0-9_-]+="[^"]*")', r'\1', html)
        html = re.sub(r'\s+', ' ', html).strip()
        return html

    def process(self, raw_html, schema):
        print(f"  [INFO] Analisando com {schema.__name__}")

        clean_text = self._clean_html(raw_html)
        schema_fields = schema.model_json_schema()
        
        input_text = clean_text[:18000]

        prompt = f"""
        Extraia as vagas do HTML abaixo seguindo este JSON: {json.dumps(schema_fields)}
        
        REGRAS:
        - Liste TODAS as vagas.
        - Identifique titulo, empresa, localizacao, salario, requisitos (DETALHADOS) e link_inscricao.
        - Empresa: use 'Desconhecida' se não achar.
        - Requisitos: extraia todas as tecnologias e soft/hard skills listadas.
        
        HTML:
        {input_text}
        """

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Assistente de extração JSON. Responda apenas o objeto JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            json_response = json.loads(response.choices[0].message.content)
            validated_data = schema(**json_response)
            
            return validated_data
        except ValidationError as e:
            print(f"  [ERROR] Validação de dados: {e}")
            return None
        except Exception as e:
            print(f"  [ERROR] Erro no processamento da IA: {e}")
            return None
