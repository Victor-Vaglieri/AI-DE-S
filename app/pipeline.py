import os
import time
import logging
import threading
from urllib.parse import urlparse
from app.logger_config import logger
from app.github_project_ex import GitHubProjectExporter 
from app.exporter import ObsidianExporter
from app.sql_exporter import SqlExporter
from app.scraper import WebScraper
from app.processor import DataProcessor
from app.schemas.jobs import JobList
from app.schemas.hardware import HardwareList
from app.settings import settings

class Pipeline:
    def __init__(self, mode="jobs", urls_file=None, config_path=None):
        # Global/Input (English)
        self.mode = mode
        self.urls_file = urls_file or (
            "config/sites-vagas.txt" if mode == "jobs" else "config/sites-hardware.txt"
        )
        self.schema = JobList if mode == "jobs" else HardwareList
        
        # Internal/Local (Portuguese - encurtado)
        out_path = settings.get("pipeline.output_path", "data/output")
        self.caminho_saida = out_path
        
        db_url = settings.get("pipeline.db_url", "sqlite:///data/ai_des.db")
        self.exporters = [
            ObsidianExporter(base_path=out_path),
            GitHubProjectExporter(),
            SqlExporter(db_url=db_url)
        ]
        
        self.processor = DataProcessor()
        self.scraper = WebScraper()
        self.itens_vistos = set()
        self._trava = threading.Lock()

    def _preparar_ambiente(self):
        os.makedirs("data", exist_ok=True)
        if os.path.exists(self.caminho_saida):
            for arq in os.listdir(self.caminho_saida):
                cam_arq = os.path.join(self.caminho_saida, arq)
                try:
                    if os.path.isfile(cam_arq):
                        os.remove(cam_arq)
                except Exception:
                    pass
        else:
            os.makedirs(self.caminho_saida, exist_ok=True)

    def _load_urls(self):
        if not os.path.exists(self.urls_file): 
            logger.error(f"Arquivo não localizado: {self.urls_file}")
            return []
        try:
            with open(self.urls_file, 'r', encoding='utf-8') as f:
                return [l.strip() for l in f if l.strip() and not l.startswith("#")]
        except Exception as e:
            logger.error(f"Erro ao ler URLs: {e}")
            return []

    def _extrair_dominio(self, url):
        try:
            dom = urlparse(url).netloc
            return dom.replace('www.', '').split('.')[0].capitalize()
        except Exception:
            return "Web"

    def run(self):
        self._preparar_ambiente()
        lista_urls = self._load_urls()
        
        logger.info("=" * 40)
        logger.info(f"AI-DE-S | MODO: {self.mode.upper()} | URLS: {len(lista_urls)}")
        logger.info("=" * 40)

        if not lista_urls: 
            logger.error("Nenhuma URL para processar.")
            return

        try:
            for idx, url in enumerate(lista_urls, 1):
                logger.info(f"[{idx}/{len(lista_urls)}] Processando: {url}")
                
                txt_bruto = self.scraper.fetch_content(url)
                if not txt_bruto:
                    logger.warning(f"Conteúdo vazio ou erro no scraping: {url}")
                    continue

                dado_estru = self.processor.process(txt_bruto, self.schema)
                if not dado_estru:
                    logger.error(f"IA falhou ao estruturar dados: {url}")
                    continue

                lista_itens = getattr(dado_estru, 'vagas', []) if self.mode == "jobs" else getattr(dado_estru, 'produtos', [])
                if not lista_itens:
                    logger.warning(f"Nenhum item válido identificado pela IA: {url}")
                    continue

                logger.info(f"Extração bem-sucedida: {len(lista_itens)} itens.")
                for item in lista_itens:
                    self._process_item(item, url)
                
                time.sleep(1) 
                
        finally:
            self.scraper.close()
            logger.info("=" * 40)
            logger.info("PIPELINE FINALIZADO")
            logger.info("=" * 40)

    def _process_item(self, item, source_url):
        # Chave para deduplicação
        if self.mode == "jobs":
            chave_item = f"{item.titulo.lower()}|{item.empresa.lower()}"
        else:
            chave_item = f"{item.produto.lower()}|{getattr(item, 'loja', 'unknown').lower()}"
        
        if chave_item in self.itens_vistos:
            logger.debug(f"Duplicata ignorada: {chave_item}")
            return
        
        self.itens_vistos.add(chave_item)

        if self.mode == "jobs":
            if "Título não encontrado" in item.titulo or not item.empresa.strip():
                return
            
            if not item.link_inscricao or "http" not in item.link_inscricao:
                url_pars = urlparse(source_url)
                link = item.link_inscricao or ""
                path = link if link.startswith('/') else f"/{link}"
                item.link_inscricao = f"{url_pars.scheme}://{url_pars.netloc}{path}"
        
            if not item.origem or item.origem.lower() in ["desconhecida", "unknown"]:
                item.origem = self._extrair_dominio(source_url)
        
        for expor in self.exporters:
            try:
                expor.save(item, self.mode)
            except Exception as e:
                logger.error(f"Erro no exportador {expor.__class__.__name__}: {e}")
