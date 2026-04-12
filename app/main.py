import os
import shutil
import time
from dotenv import load_dotenv

from github_project_ex import GitHubProjectExporter 
from exporter import ObsidianExporter
from scraper import WebScraper
from schemas.jobs import JobList
from schemas.hardware import HardwareList
from processor import DataProcessor
from urllib.parse import urlparse

load_dotenv()

obsidian_exporter = ObsidianExporter()
github_exporter = GitHubProjectExporter()

def preparar_ambiente(pasta="data/output"):
    if os.path.exists(pasta):
        for arquivo in os.listdir(pasta):
            caminho_arquivo = os.path.join(pasta, arquivo)
            try:
                if os.path.isfile(caminho_arquivo):
                    os.remove(caminho_arquivo)
            except Exception as e:
                pass
    else:
        os.makedirs(pasta, exist_ok=True)

def get_config():
    mode = os.getenv("TARGET_MODE", "jobs").lower()
    configs = {
        "jobs": {"schema": JobList, "url_file": "config/sites-vagas.txt"},
        "hardware": {"schema": HardwareList, "url_file": "config/sites-hardware.txt"}
    }
    if mode not in configs: raise ValueError(mode)
    return mode, configs[mode]["schema"], configs[mode]["url_file"]

def load_urls(filepath):
    if not os.path.exists(filepath): return []
    with open(filepath, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    
def extrair_dominio(url):
    try:
        domain = urlparse(url).netloc
        name = domain.replace('www.', '').split('.')[0]
        return name.capitalize()
    except:
        return "Web"

def main():
    preparar_ambiente()
    processor_instancia = DataProcessor()
    mode, schema, url_file = get_config()
    urls = load_urls(url_file)
    
    print("\n" + "-"*60)
    print(f" AI-DE-S | MODO: {mode.upper()}")
    print(f" SOURCE: {url_file} | URLS: {len(urls)}")
    print("-"*60)

    if not urls: 
        print("[ERROR] Nenhuma URL encontrada para processar.")
        return

    scraper = WebScraper()
    
    try:
        for idx, url in enumerate(urls, 1):
            print(f"\n[PROCESS] ({idx}/{len(urls)}) {url[:60]}...")
            
            raw_text = scraper.fetch_content(url)
            
            if raw_text:
                structured_data = processor_instancia.process(raw_text, schema)
                
                if structured_data:
                    items = getattr(structured_data, 'vagas', []) if mode == "jobs" else getattr(structured_data, 'produtos', [])

                    if isinstance(items, list) and len(items) > 0:
                        print(f"  [SUCCESS] Encontrados {len(items)} itens.")
                        for item in items:
                            if mode == "jobs":
                                if "Título não encontrado" in item.titulo or "Nenhuma vaga" in item.titulo:
                                    continue
                                
                                if "Empresa não informada" in item.empresa or not item.empresa.strip():
                                    print(f"  [SKIP] Vaga ignorada por falta de nome da empresa: {item.titulo}")
                                    continue
                            
                                if not item.link_inscricao or "http" not in item.link_inscricao:
                                    parsed_uri = urlparse(url)
                                    base_url = f"{parsed_uri.scheme}://{parsed_uri.netloc}"
                                    path = item.link_inscricao if item.link_inscricao else ""
                                    if not path.startswith("/"): path = "/" + path
                                    item.link_inscricao = base_url + path
                           
                                if not item.origem or item.origem.lower() in ["desconhecida", "unknown"]:
                                    item.origem = extrair_dominio(url)
                                
                                github_exporter.save(item, mode) 
                                
                            obsidian_exporter.save(item, mode)                       
                    else:
                        print(f"  [WARNING] Nenhum item relevante extraído desta página.")
                else:
                    print(f"  [ERROR] Falha na análise da IA para esta URL.")
            else:
                print(f"  [ERROR] Não foi possível obter o conteúdo da página.")
            
            time.sleep(2) 
            
    finally:
        scraper.close()
        print("\n" + "-"*60)
        print(" EXECUÇÃO FINALIZADA")
        print("-"*60 + "\n")

if __name__ == "__main__":
    main()
