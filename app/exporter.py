import os
from datetime import datetime

class ObsidianExporter:
    def __init__(self, base_path="data/output"):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)

    def save(self, structured_data, mode):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        raw_name = getattr(structured_data, 'titulo', getattr(structured_data, 'produto', 'extracao'))
        clean_name = "".join([c for c in raw_name if c.isalnum() or c in (' ', '_')]).rstrip()
        filename = f"{mode}_{clean_name}_{timestamp}.md".replace(" ", "_")
        file_path = os.path.join(self.base_path, filename)
        
        data_dict = structured_data.model_dump()
        
        lines = ["---"]
        for key, value in data_dict.items():
            lines.append(f"{key}: {value}")
        lines.append(f"extraido_em: {datetime.now().isoformat()}")
        lines.append(f"nicho: {mode}")
        lines.append("---")
        
        lines.append(f"\n# {raw_name}")
        
        # Lógica para Template de Mensagem LinkedIn
        if mode == "jobs":
            requisitos = ", ".join(data_dict.get('requisitos', []))
            empresa = data_dict.get('empresa', 'sua empresa')
            vaga = data_dict.get('titulo', 'esta vaga')
            
            mensagem = (
                f"\n## 📩 Mensagem para o Recrutador\n"
                f"> Olá recrutador, acabei de me inscrever na vaga **{vaga}** na **{empresa}** "
                f"e gostaria de destacar por aqui as minhas características que ajudam na contratação: "
                f"{requisitos}. Desde já agradeço."
            )
            lines.append(mensagem)

        lines.append(f"\n\n--- \n*Extração automática realizada em {datetime.now().strftime('%d/%m/%Y')}.*")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"sucesso: {file_path}")
        return file_path