import os
from datetime import datetime

class ObsidianExporter:
    def __init__(self, base_path="data/output"):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)

    def save(self, structured_data, mode):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        raw_name = getattr(structured_data, 'titulo', getattr(structured_data, 'produto', 'extração'))
        clean_name = "".join([c for c in raw_name if c.isalnum() or c in (' ', '_')]).rstrip()
        filename = f"{mode}_{clean_name}_{timestamp}.md".replace(" ", "_")
        file_path = os.path.join(self.base_path, filename)
        data_dict = structured_data.model_dump()
        
        lines = ["---"]
        for key, value in data_dict.items():
            lines.append(f"{key}: {value}")
        lines.append(f"extraido_em: {datetime.now().isoformat()}")
        lines.append(mode)
        lines.append("\n---\n")
        
        lines.append(f"# {raw_name}")
        lines.append(f"\nResumo da extração automática realizada em {datetime.now().strftime('%d/%m/%Y')}.")

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            print(f"sucesso: {file_path}")
            return file_path
        except Exception as e:
            print(f"erro: {e}")
            return None