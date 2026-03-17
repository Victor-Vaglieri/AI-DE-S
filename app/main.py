import os
from dotenv import load_dotenv
from scraper import WebScraper
from schemas.jobs import JobListing
from schemas.hardware import HardwarePrice
import processor
import exporter

load_dotenv()

def get_config():
    """Centraliza a lógica de troca de contexto."""
    mode = os.getenv("TARGET_MODE", "jobs").lower()
    
    configs = {
        "jobs": {
            "schema": JobListing,
            "url_file": "config/sites-vagas.txt"
        },
        "hardware": {
            "schema": HardwarePrice,
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
    mode, schema, url_file = get_config()
    
    urls = load_urls(url_file)
    
    print(f"{mode.upper()}")
    print(f"{url_file}")
    print(f"{schema.__name__}")

    if not urls:
        return

    scraper = WebScraper()
    
    try:
        for idx, url in enumerate(urls, 1):
            print(f"\n--- [{idx}/{len(urls)}] Scrapeando: {url} ---")
            raw_text = scraper.fetch_content(url)
            
            if raw_text:
                print(f"{10 * ' '}{mode}: {raw_text[:200]}\n") 
                structured_data = processor.process(raw_text, schema)
                if structured_data:
                    print(f"SUCESSO: {structured_data.model_dump_json(indent=2)}")
                    
                    exporter.save(structured_data, mode) 
                else:
                    print(f"ERRO: {url}")
            
    finally:
        scraper.close()
        print("\nFim da execução.")

if __name__ == "__main__":
    main()