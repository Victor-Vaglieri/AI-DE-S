import os
from dotenv import load_dotenv
from exporter import ObsidianExporter
from scraper import WebScraper
from schemas.jobs import JobListing
from schemas.hardware import HardwarePrice, HardwareList
from processor import DataProcessor

exporter = ObsidianExporter()
load_dotenv()

import shutil

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
        "jobs": {
            "schema": JobListing, 
            "url_file": "config/sites-vagas.txt"
        },
        "hardware": {
            "schema": HardwareList, 
            "url_file": "config/sites-hardware.txt"
        }
    }
    
    if mode not in configs:
        raise ValueError(mode)
        
    return mode, configs[mode]["schema"], configs[mode]["url_file"]

def load_urls(filepath):
    if not os.path.exists(filepath):
        print(f"Arquivo não encontrado: {filepath}")
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

def main():
    preparar_ambiente()
    processor_instancia = DataProcessor()
    mode, schema, url_file = get_config()
    
    urls = load_urls(url_file)
    
    print(f"MODO: {mode.upper()} | SCHEMA: {schema.__name__}")

    if not urls:
        return

    scraper = WebScraper()
    
    try:
        for idx, url in enumerate(urls, 1):
            print(f"\n--- [{idx}/{len(urls)}] Scrapeando: {url} ---")
            raw_text = scraper.fetch_content(url)
            
            if raw_text:
                structured_data = processor_instancia.process(raw_text, schema)
                
                if structured_data:
                    if mode == "hardware" and hasattr(structured_data, 'produtos'):
                        print(f"✅ Encontrados {len(structured_data.produtos)} produtos.")
                        for item in structured_data.produtos:
                            exporter.save(item, mode)
                    else:
                        exporter.save(structured_data, mode)
                else:
                    print(f"ERRO: A IA não retornou dados válidos para {url}")
            
    finally:
        scraper.close()
        del scraper
        print("\nFim da execução.")

if __name__ == "__main__":
    main()