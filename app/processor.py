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
        """Remoção máxima de ruído HTML preservando estrutura semântica e atributos de dados."""
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
        print(f"  [INFO] Analisando com {schema.__name__}")

        clean_text = self._clean_html(raw_html)
        schema_json = schema.model_json_schema()
        input_text = clean_text[:20000]

        prompt = f"""
        Você é um assistente especializado em extração de dados estruturados.
        Analise o HTML abaixo e extraia as informações seguindo EXATAMENTE este schema JSON:
        {json.dumps(schema_json, indent=2)}

        REGRAS CRÍTICAS:
        1. Se um campo não for encontrado, use o valor default especificado no schema.
        2. Para listas, se não houver itens, retorne uma lista vazia [].
        3. No caso de Preços de Hardware, certifique-se de extrair o valor numérico puro para campos float.
        4. Responda APENAS com o objeto JSON válido, sem explicações.

        HTML:
        {input_text}
        """

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Assistente de extração JSON de alta precisão."},
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
