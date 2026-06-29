import os
import asyncio
import logging
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from pydantic import ValidationError
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.logger_config import logger
from app.github_project_ex import GitHubProjectExporter 
from app.exporter import ObsidianExporter
from app.sql_exporter import SqlExporter
from app.scraper import WebScraper
from app.processor import DataProcessor
from app.schemas.jobs import JobList
from app.settings import settings

class Pipeline:
    def __init__(self, urls_file=None, config_path=None):
        self.urls_file = urls_file or "config/sites-vagas.txt"
        self.schema = JobList
        
        self.output_path = settings.get("pipeline.output_path", "data/output")
        db_url = settings.get("pipeline.db_url", "sqlite:///data/ai_des.db")
        
        self.exporters = [
            ObsidianExporter(base_path=self.output_path),
            GitHubProjectExporter(),
            SqlExporter(db_url=db_url)
        ]
        
        self.processor = DataProcessor()
        self.seen_items = set()
        self._lock = asyncio.Lock()

    def _prepare_environment(self):
        os.makedirs("data", exist_ok=True)
        if os.path.exists(self.output_path):
            for filename in os.listdir(self.output_path):
                filepath = os.path.join(self.output_path, filename)
                try:
                    if os.path.isfile(filepath):
                        os.remove(filepath)
                except Exception:
                    pass
        else:
            os.makedirs(self.output_path, exist_ok=True)

    def _load_urls(self):
        if not os.path.exists(self.urls_file): 
            logger.error(f"Arquivo não localizado: {self.urls_file}")
            return []
        try:
            with open(self.urls_file, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip() and not line.startswith("#")]
        except Exception as e:
            logger.error(f"Erro ao ler URLs: {e}")
            return []

    def _extract_domain(self, url):
        try:
            domain = urlparse(url).netloc
            return domain.replace('www.', '').split('.')[0].capitalize()
        except Exception:
            return "Web"

    def _is_job_recent(self, time_tag):
        """Verifica se a vaga é recente baseada na tag de tempo."""
        dt_str = time_tag.get('datetime')
        if dt_str:
            try:
                job_date = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                job_date = job_date.replace(tzinfo=None)
                age = datetime.now() - job_date
                
                if age > timedelta(days=1, hours=12):
                    return False
                return True
            except Exception:
                pass
                
        time_text = time_tag.get_text(strip=True).lower()
        
        if re.search(r'\b(week|month|year|semana|mês|mes|ano)s?\b', time_text):
            return False
        
        if re.search(r'\b(?:[2-9]|[1-9]\d+)\s+(day|dia)s?\b', time_text):
            return False
            
        return True

    async def process_url(self, url, current_index, total, semaphore):
        async with semaphore:
            logger.info(f"[{current_index}/{total}] Iniciando captura: {url}")
            scraper = WebScraper()
            
            try:
                raw_text = await scraper.fetch_content(url)
                if not raw_text:
                    logger.warning(f"[{current_index}/{total}] Conteúdo vazio ou erro: {url}")
                    return

                soup = BeautifulSoup(raw_text, 'lxml')
                job_links = []
                cards = soup.select('.job-search-card, .base-search-card, li')
                
                if cards:
                    for card in cards:
                        a_tag = card.select_one('a.base-card__full-link, a.job-search-card__link, a[href*="/job/"], a[href*="/vaga/"]')
                        if not a_tag:
                            continue
                            
                        href = a_tag.get('href')
                        if not href or 'http' not in href or href in job_links:
                            continue
                        
                        time_tag = card.select_one('time')
                        if time_tag and not self._is_job_recent(time_tag):
                            logger.debug(f"[{current_index}/{total}] Ignorando vaga antiga: {href}")
                            continue
                                
                        job_links.append(href)
                
                if not job_links:
                    for a_tag in soup.select('a.base-card__full-link, a.job-search-card__link, a[href*="/job/"], a[href*="/vaga/"]'):
                        href = a_tag.get('href')
                        if href and href not in job_links and 'http' in href:
                            job_links.append(href)
                
                if job_links and len(job_links) > 1:
                    logger.info(f"[{current_index}/{total}] Encontrados {len(job_links)} links de vagas. Extraindo detalhes de todas (em lotes).")
                    batch_size = settings.get("pipeline.job_batch_size", 5)
                    batch_semaphore = asyncio.Semaphore(5)

                    async def extract_job_safe(job_url):
                        async with batch_semaphore:
                            try:
                                job_html = await scraper.fetch_content(job_url, fast_mode=True)
                                clean_job_text = self.processor._clean_html_soup(job_html)
                                return f"URL: {job_url}\n{clean_job_text}"
                            except Exception as e:
                                logger.error(f"Erro ao extrair link de vaga {job_url}: {e}")
                                return None

                    for i in range(0, len(job_links), batch_size):
                        batch_links = job_links[i:i+batch_size]
                        logger.info(f"[{current_index}/{total}] Baixando HTML do lote {i//batch_size + 1} ({len(batch_links)} vagas) concorrentemente...")
                        
                        html_results = await asyncio.gather(*[extract_job_safe(u) for u in batch_links])
                        job_texts = [res for res in html_results if res]
                        
                        final_text = "\n\n=== NOVA VAGA ===\n\n".join(job_texts)
                        
                        try:
                            structured_data = await self.processor.process(final_text, self.schema)
                            if structured_data and getattr(structured_data, 'vagas', []):
                                job_items = structured_data.vagas
                                logger.info(f"[{current_index}/{total}] Lote {i//batch_size + 1} processado: {len(job_items)} itens.")
                                for item in job_items:
                                    await self._process_item(item, url)
                            else:
                                logger.warning(f"[{current_index}/{total}] Nenhum item identificado no lote {i//batch_size + 1}.")
                        except ValidationError as ve:
                            logger.error(f"[{current_index}/{total}] IA retornou formato inválido no lote {i//batch_size + 1}: {ve}")
                        except Exception as e:
                            logger.error(f"[{current_index}/{total}] IA falhou ao estruturar o lote {i//batch_size + 1}: {e}")
                else:
                    try:
                        structured_data = await self.processor.process(raw_text, self.schema)
                        if not structured_data or not getattr(structured_data, 'vagas', []):
                            logger.warning(f"[{current_index}/{total}] Nenhum item identificado: {url}")
                            return

                        job_items = structured_data.vagas
                        logger.info(f"[{current_index}/{total}] Sucesso: {len(job_items)} itens de {url}")
                        for item in job_items:
                            await self._process_item(item, url)
                    except ValidationError as ve:
                        logger.error(f"[{current_index}/{total}] Validação de dados falhou: {ve}")
                        return
                    
            except PlaywrightTimeoutError:
                logger.error(f"[{current_index}/{total}] Timeout do navegador na URL: {url}")
            except Exception as e:
                logger.error(f"[{current_index}/{total}] Erro inesperado na tarefa principal da URL: {e}")

    async def run(self):
        self._prepare_environment()
        urls_list = self._load_urls()
        
        logger.info("=" * 40)
        max_workers = settings.get("pipeline.max_workers", 3)
        logger.info(f"AI-DE-S | MODO: JOBS | URLS: {len(urls_list)} | PARALELISMO: {max_workers}")
        logger.info("=" * 40)

        if not urls_list: 
            logger.error("Nenhuma URL para processar.")
            return

        semaphore = asyncio.Semaphore(max_workers)
        total_urls = len(urls_list)
        
        tasks = []
        for index, url in enumerate(urls_list, 1):
            tasks.append(self.process_url(url, index, total_urls, semaphore))
        
        await asyncio.gather(*tasks)
        await WebScraper.close_browser()
        
        logger.info("=" * 40)
        logger.info("PIPELINE FINALIZADO")
        logger.info("=" * 40)

    async def _process_item(self, item, source_url):
        item_key = f"{item.titulo.lower()}|{item.empresa.lower()}"

        async with self._lock:
            if item_key in self.seen_items:
                logger.debug(f"Duplicata ignorada: {item_key}")
                return
            self.seen_items.add(item_key)

        if not item.titulo or not item.titulo.strip() or not item.empresa or not item.empresa.strip():
            return
        
        if not item.link_inscricao or "http" not in item.link_inscricao:
            url_parsed = urlparse(source_url)
            link_inst = item.link_inscricao or ""
            path_inst = link_inst if link_inst.startswith('/') else f"/{link_inst}"
            item.link_inscricao = f"{url_parsed.scheme}://{url_parsed.netloc}{path_inst}"
    
        if not item.origem or item.origem.lower() in ["desconhecida", "unknown"]:
            item.origem = self._extract_domain(source_url)
        
        for exporter in self.exporters:
            try:
                await asyncio.to_thread(exporter.save, item, "jobs")
            except Exception as e:
                logger.error(f"Erro no exportador {exporter.__class__.__name__}: {e}")
