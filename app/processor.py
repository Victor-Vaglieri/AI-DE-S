import os
import json
from groq import Groq
from pydantic import ValidationError

class DataProcessor:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("chave não encontrada")
        
        self.client = Groq(api_key=self.api_key)

    def process(self, raw_text, schema):
        print(f"analisando: {schema.__name__}")

        schema_fields = schema.model_json_schema()
        
        prompt = f"""
        Você é um extrator de dados especializado. Sua tarefa é extrair informações do texto bruto abaixo.
        Siga estas regras:
        1. Responda APENAS com um objeto JSON válido.
        2. Se a informação não for encontrada, use null ou uma lista vazia, conforme o tipo do campo.
        3. Use o seguinte esquema JSON como guia para os campos: {json.dumps(schema_fields)}
        4. Se você não encontrar o nome da loja no texto, use 'Desconhecida'. 
        5. Não deixe o campo 'loja' como null.

        Texto Bruto:
        {raw_text[:12000]}
        """

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Você é um assistente que extrai dados e responde apenas em JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            json_response = json.loads(response.choices[0].message.content)
            validated_data = schema(**json_response)
            
            return validated_data

        except ValidationError as e:
            print(f"validação de dados: {e}")
            return None
        except Exception as e:
            print(f"Erro no processamento: {e}")
            return None