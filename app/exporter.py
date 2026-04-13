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
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        raw_name = getattr(structured_data, 'titulo' if mode == "jobs" else 'produto', 'item')
        empresa = getattr(structured_data, 'empresa', 'empresa')
        
        clean_name = "".join([c for c in raw_name if c.isalnum() or c in (' ', '_')]).strip().replace(" ", "_")
        filename = f"{mode}_{clean_name}_{timestamp}.md"
        file_path = os.path.join(self.base_path, filename)
        
        data_dict = structured_data.model_dump()
        lines = ["---"]
        for k, v in data_dict.items():
            if k != 'requisitos': lines.append(f"{k}: {v}")
        lines.append(f"extraido_em: {datetime.now().isoformat()}\nnicho: {mode}\n---\n")
        lines.append(f"# {raw_name} @ {empresa if mode == 'jobs' else ''}")

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            logger.info("Arquivo Obsidian salvo.")
        except Exception as e:
            logger.error(f"Erro Obsidian: {e}")
            
        return file_path
