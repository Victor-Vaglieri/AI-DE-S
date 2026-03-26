import os
from datetime import datetime

class ObsidianExporter:
    def __init__(self, base_path="data/output"):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)

    def save(self, structured_data, mode):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

        if mode == "jobs":
            raw_name = getattr(structured_data, 'titulo', 'vaga')
            empresa = getattr(structured_data, 'empresa', 'empresa')
            display_title = f"{raw_name} @ {empresa}"
        else:
            raw_name = getattr(structured_data, 'produto', 'extracao')
            display_title = raw_name

        clean_name = "".join([c for c in raw_name if c.isalnum() or c in (' ', '_')]).strip().replace(" ", "_")
        filename = f"{mode}_{clean_name}_{timestamp}.md"
        file_path = os.path.join(self.base_path, filename)
        
        data_dict = structured_data.model_dump()
        
        lines = ["---"]
        for key, value in data_dict.items():
            if key not in ['requisitos']: 
                lines.append(f"{key}: {value}")
        lines.append(f"extraido_em: {datetime.now().isoformat()}")
        lines.append(f"nicho: {mode}")
        lines.append("---")
        

        lines.append(f"\n# 📌 {display_title}")
        
        if mode == "jobs":
            lines.append(f"\n### Empresa: {data_dict.get('empresa', 'Não informada')}")
            lines.append(f"**Local:** {data_dict.get('localizacao', 'Não informado')}")
            lines.append(f"**Salário:** {data_dict.get('salario', 'Não informado')}")
            lines.append(f"**Link:** [{data_dict.get('origem', 'Inscrição')}]({data_dict.get('link_inscricao', '#')})")
            
            lines.append("\n### 🛠️ Requisitos & Tech Stack")
            requisitos = data_dict.get('requisitos', [])
            if requisitos:
                for req in requisitos:
                    lines.append(f"- {req}")
            else:
                lines.append("- Não listado explicitamente.")

            req_string = ", ".join(requisitos) if requisitos else "minhas habilidades"
            mensagem = (
                f"\n---\n## Mensagem para o Recrutador\n"
                f"> Olá recrutador, acabei de me inscrever na vaga **{raw_name}** na **{empresa}** "
                f"e gostaria de destacar por aqui as minhas características que ajudam na contratação: "
                f"**{req_string}**. Desde já agradeço."
            )
            lines.append(mensagem)
        
        elif mode == "hardware":
            lines.append(f"\n### 💰 Preço à Vista: R$ {data_dict.get('preco_vista', '0.00')}")
            lines.append(f"**Parcelado:** R$ {data_dict.get('preco_parcelado', '0.00')}")
            lines.append(f"**Loja:** {data_dict.get('loja', 'Desconhecida')}")
            lines.append(f"**Estoque:** {'Sim' if data_dict.get('em_estoque') else 'Não'}")

        lines.append(f"\n\n--- \n*Extração automática realizada em {datetime.now().strftime('%d/%m/%Y %H:%M')}.*")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"  [SUCCESS] Arquivo salvo: {filename}")
        return file_path