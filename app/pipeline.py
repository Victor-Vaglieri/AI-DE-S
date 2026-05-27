import os
import asyncio
import logging
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
        self.mode = mode
        self.urls_file = urls_file or (
            "config/sites-vagas.txt" if mode == "jobs" else "config/sites-hardware.txt"
        )
        self.schema = JobList if mode == "jobs" else HardwareList
        
        out_path = settings.get("pipeline.output_path", "data/output")
        self.caminho_saida = out_path
        
        db_url = settings.get("pipeline.db_url", "sqlite:///data/ai_des.db")
        self.exporters = [
            ObsidianExporter(base_path=out_path),
            GitHubProjectExporter(),
            SqlExporter(db_url=db_url)
        ]
        
        self.processor = DataProcessor()
        self.itens_vistos = set()
        self._trava = asyncio.Lock()

    def _preparar_ambiente(self):
        os.makedirs("data", exist_ok=True)
        if os.path.exists(self.caminho_saida):
            for arquiv in os.listdir(self.caminho_saida):
                caminh_arq = os.path.join(self.caminho_saida, arquiv)
                try:
                    if os.path.isfile(caminh_arq):
                        os.remove(caminh_arq)
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
                return [linha.strip() for linha in f if linha.strip() and not linha.startswith("#")]
        except Exception as e:
            logger.error(f"Erro ao ler URLs: {e}")
            return []

    def _extrair_dominio(self, url):
        try:
            dominio_url = urlparse(url).netloc
            return dominio_url.replace('www.', '').split('.')[0].capitalize()
        except Exception:
            return "Web"

    async def process_url(self, url, indice_at, total, semaphore):
        async with semaphore:
            logger.info(f"[{indice_at}/{total}] Iniciando captura: {url}")
            navegador = WebScraper()
            
            try:
                texto_bruto = await navegador.fetch_content(url)
                if not texto_bruto:
                    logger.warning(f"[{indice_at}/{total}] Conteúdo vazio ou erro: {url}")
                    return

                dados_estru = await self.processor.process(texto_bruto, self.schema)
                if not dados_estru:
                    logger.error(f"[{indice_at}/{total}] IA falhou ao estruturar: {url}")
                    return

                lista_itens = getattr(dados_estru, 'vagas', []) if self.mode == "jobs" else getattr(dados_estru, 'produtos', [])
                if not lista_itens:
                    logger.warning(f"[{indice_at}/{total}] Nenhum item identificado: {url}")
                    return

                logger.info(f"[{indice_at}/{total}] Sucesso: {len(lista_itens)} itens de {url}")
                for item in lista_itens:
                    await self._process_item(item, url)
                    
            except Exception as e:
                logger.error(f"[{indice_at}/{total}] Erro inesperado na tarefa: {e}")

    async def run(self):
        self._preparar_ambiente()
        lista_urls = self._load_urls()
        
        logger.info("=" * 40)
        num_trabalhadores = settings.get("pipeline.max_workers", 3)
        logger.info(f"AI-DE-S | MODO: {self.mode.upper()} | URLS: {len(lista_urls)} | PARALELISMO: {num_trabalhadores}")
        logger.info("=" * 40)

        if not lista_urls: 
            logger.error("Nenhuma URL para processar.")
            return

        semaphore = asyncio.Semaphore(num_trabalhadores)
        total_urls = len(lista_urls)
        
        tarefas = []
        for indice_at, url in enumerate(lista_urls, 1):
            tarefas.append(self.process_url(url, indice_at, total_urls, semaphore))
        
        await asyncio.gather(*tarefas)
        await WebScraper.close_browser()
        
        logger.info("=" * 40)
        logger.info("PIPELINE FINALIZADO")
        logger.info("=" * 40)

    async def _process_item(self, item, source_url):
        # Chave para deduplicação
        if self.mode == "jobs":
            chave_item = f"{item.titulo.lower()}|{item.empresa.lower()}"
        else:
            chave_item = f"{item.produto.lower()}|{getattr(item, 'loja', 'unknown').lower()}"

        async with self._trava:
            if chave_item in self.itens_vistos:
                logger.debug(f"Duplicata ignorada: {chave_item}")
                return
            self.itens_vistos.add(chave_item)

        if self.mode == "jobs":
            if "Título não encontrado" in item.titulo or not item.empresa.strip():
                return
            
            if not item.link_inscricao or "http" not in item.link_inscricao:
                url_parsed = urlparse(source_url)
                link_inst = item.link_inscricao or ""
                path_inst = link_inst if link_inst.startswith('/') else f"/{link_inst}"
                item.link_inscricao = f"{url_parsed.scheme}://{url_parsed.netloc}{path_inst}"
        
            if not item.origem or item.origem.lower() in ["desconhecida", "unknown"]:
                item.origem = self._extrair_dominio(source_url)
        
        for exportador in self.exporters:
            try:
                await asyncio.to_thread(exportador.save, item, self.mode)
            except Exception as e:
                logger.error(f"Erro no exportador {exportador.__class__.__name__}: {e}")

