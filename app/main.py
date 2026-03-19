import os
import shutil
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
                print(f"Erro ao limpar arquivo {arquivo}: {e}")
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
    
    print(f"MODO: {mode.upper()} | SCHEMA: {schema.__name__}")

    if not urls: return

    scraper = WebScraper()
    
    try:
        for idx, url in enumerate(urls, 1):
            print(f"\n--- [{idx}/{len(urls)}] Scrapeando: {url} ---")
            raw_text = scraper.fetch_content(url)
            
            if raw_text:
                structured_data = processor_instancia.process(raw_text, schema)
                
                if structured_data:
                    items = getattr(structured_data, 'produtos', getattr(structured_data, 'vagas', None))

                    if items and isinstance(items, list):
                        print(f"✅ Encontrados {len(items)} itens.")
                        for item in items:
                            if mode == "jobs" and (not item.link_inscricao or item.link_inscricao == "None"):
                                item.link_inscricao = url
                            invalidos = ["desconhecida", "unknown", "none", "", None]
                            origem_atual = str(getattr(item, 'origem', "")).lower()
                            if origem_atual in invalidos:
                                item.origem = extrair_dominio(url)
                            obsidian_exporter.save(item, mode)
                            if mode == "jobs":
                                github_exporter.save(item, mode) 
                    else:
                        obsidian_exporter.save(structured_data, mode)
                        github_exporter.save(structured_data, mode)
                else:
                    print(f"ERRO: A IA não retornou dados válidos para {url}")
            
    finally:
        scraper.close()
        print("\nFim da execução.")

if __name__ == "__main__":
    main()