import os
from datetime import datetime
import logging
from app.exporters_base import BaseExporter

logger = logging.getLogger("AI-DE-S.Obsidian")

class ObsidianExporter(BaseExporter):
    def __init__(self, base_path="data/output"):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)

    def save(self, structured_data, mode):
        marca_tempo = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        nome_bruto = getattr(structured_data, 'titulo' if mode == "jobs" else 'produto', 'item')
        empresa_item = getattr(structured_data, 'empresa', 'empresa')
        
        nome_limpo = "".join([c for c in nome_bruto if c.isalnum() or c in (' ', '_')]).strip().replace(" ", "_")
        nome_arquiv = f"{mode}_{nome_limpo}_{marca_tempo}.md"
        caminh_arquiv = os.path.join(self.base_path, nome_arquiv)
        
        dicion_dados = structured_data.model_dump()
        linhas_texto = ["---"]
        for chave_atua, valor_atua in dicion_dados.items():
            if chave_atua != 'requisitos': linhas_texto.append(f"{chave_atua}: {valor_atua}")
        linhas_texto.append(f"extraido_em: {datetime.now().isoformat()}\nnicho: {mode}\n---\n")
        linhas_texto.append(f"# {nome_bruto} @ {empresa_item if mode == 'jobs' else ''}")

        try:
            with open(caminh_arquiv, "w", encoding="utf-8") as f:
                f.write("\n".join(linhas_texto))
            logger.debug(f"Obsidian: Salvo em {nome_arquiv}")
        except Exception as e:
            logger.error(f"Erro Obsidian: {e}")
            
        return caminh_arquiv
