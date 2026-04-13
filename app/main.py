import os
import time
from dotenv import load_dotenv
from urllib.parse import urlparse
import logging
from app.logger_config import logger
from app.github_project_ex import GitHubProjectExporter 
from app.exporter import ObsidianExporter
from app.sql_exporter import SqlExporter
from app.scraper import WebScraper
from app.schemas.jobs import JobList
from app.schemas.hardware import HardwareList
from app.processor import DataProcessor

load_dotenv()

exporters = [
    ObsidianExporter(),
    GitHubProjectExporter(),
    SqlExporter()
]

def preparar_ambiente(pasta="data/output"):
    os.makedirs("data", exist_ok=True)
    if os.path.exists(pasta):
        for arquivo in os.listdir(pasta):
            caminho_arquivo = os.path.join(pasta, arquivo)
            try:
                if os.path.isfile(caminho_arquivo):
                    os.remove(caminho_arquivo)
            except Exception:
                pass
    else:
        os.makedirs(pasta, exist_ok=True)

def get_config():
    mode = os.getenv("TARGET_MODE", "jobs").lower()
    configs = {
        "jobs": {"schema": JobList, "url_file": "config/sites-vagas.txt"},
        "hardware": {"schema": HardwareList, "url_file": "config/sites-hardware.txt"}
    }
    if mode not in configs: 
        logger.critical(f"Modo invalido: {mode}")
        raise ValueError(mode)
    return mode, configs[mode]["schema"], configs[mode]["url_file"]

def load_urls(filepath):
    if not os.path.exists(filepath): return []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    except Exception as e:
        logger.error(f"Erro ao carregar URLs: {e}")
        return []
    
def extrair_dominio(url):
    try:
        domain = urlparse(url).netloc
        return domain.replace('www.', '').split('.')[0].capitalize()
    except Exception:
        return "Web"

def main():
    preparar_ambiente()
    processor_instancia = DataProcessor()
    mode, schema, url_file = get_config()
    urls = load_urls(url_file)
    
    logger.info("-" * 40)
    logger.info(f"AI-DE-S | MODO: {mode.upper()} | URLS: {len(urls)}")
    logger.info("-" * 40)

    if not urls: 
        logger.error("Sem URLs para processar.")
        return

    scraper = WebScraper()
    
    try:
        for idx, url in enumerate(urls, 1):
            logger.info(f"({idx}/{len(urls)}) {url}")
            
            raw_text = scraper.fetch_content(url)
            if not raw_text:
                logger.error("Falha ao obter conteudo.")
                continue

            structured_data = processor_instancia.process(raw_text, schema)
            if not structured_data:
                logger.error("Falha na analise da IA.")
                continue

            items = getattr(structured_data, 'vagas', []) if mode == "jobs" else getattr(structured_data, 'produtos', [])
            if not items:
                logger.warning("Nenhum item encontrado.")
                continue

            logger.info(f"Sucesso: {len(items)} itens extraidos.")
            for item in items:
                if mode == "jobs":
                    if "Titulo nao encontrado" in item.titulo or not item.empresa.strip():
                        continue
                    
                    if not item.link_inscricao or "http" not in item.link_inscricao:
                        parsed = urlparse(url)
                        link = item.link_inscricao or ""
                        path = link if link.startswith('/') else f"/{link}"
                        item.link_inscricao = f"{parsed.scheme}://{parsed.netloc}{path}"
               
                    if not item.origem or item.origem.lower() in ["desconhecida", "unknown"]:
                        item.origem = extrair_dominio(url)
                
                for exporter in exporters:
                    try:
                        exporter.save(item, mode)
                    except Exception as e:
                        logger.error(f"Erro no exportador {exporter.__class__.__name__}: {e}")
            
            time.sleep(1) 
            
    finally:
        scraper.close()
        logger.info("-" * 40)
        logger.info("FINALIZADO")
        logger.info("-" * 40)

if __name__ == "__main__":
    main()
