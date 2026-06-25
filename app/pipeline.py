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
from app.settings import settings
from pydantic import ValidationError
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

class Pipeline:
    def __init__(self, urls_file=None, config_path=None):
        self.urls_file = urls_file or "config/sites-vagas.txt"
        self.schema = JobList
        
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

                from bs4 import BeautifulSoup
                sopa = BeautifulSoup(texto_bruto, 'lxml')
                
                job_links = []
                cards = sopa.select('.job-search-card, .base-search-card, li')
                
                if cards:
                    for card in cards:
                        a_tag = card.select_one('a.base-card__full-link, a.job-search-card__link, a[href*="/job/"], a[href*="/vaga/"]')
                        if not a_tag:
                            continue
                            
                        href = a_tag.get('href')
                        if not href or 'http' not in href or href in job_links:
                            continue
                        
                        # Não gostei disso
                        time_tag = card.select_one('time')
                        if time_tag:
                            valida_idade = True
                            dt_str = time_tag.get('datetime')
                            if dt_str:
                                try:
                                    from datetime import datetime, timedelta, timezone
                                    data_vaga = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                                    data_vaga = data_vaga.replace(tzinfo=None)
                                    idade = datetime.now() - data_vaga
                                    
                                    if idade > timedelta(days=1, hours=12):
                                        logger.debug(f"[{indice_at}/{total}] Ignorando vaga postada em {dt_str} (idade: {idade}).")
                                        continue
                                    valida_idade = False
                                except Exception:
                                    pass
                                    
                            if valida_idade:
                                import re
                                tempo_texto = time_tag.get_text(strip=True).lower()
                                
                                if re.search(r'\b(week|month|year|semana|mês|mes|ano)s?\b', tempo_texto):
                                    logger.debug(f"[{indice_at}/{total}] Ignorando vaga antiga (regex): {tempo_texto}")
                                    continue
                                
                                if re.search(r'\b(?:[2-9]|[1-9]\d+)\s+(day|dia)s?\b', tempo_texto):
                                    logger.debug(f"[{indice_at}/{total}] Ignorando vaga >24h (regex): {tempo_texto}")
                                    continue
                                
                        job_links.append(href)
                
                if not job_links:
                    for a_tag in sopa.select('a.base-card__full-link, a.job-search-card__link, a[href*="/job/"], a[href*="/vaga/"]'):
                        href = a_tag.get('href')
                        if href and href not in job_links and 'http' in href:
                            job_links.append(href)
                
                if job_links and len(job_links) > 1:
                    logger.info(f"[{indice_at}/{total}] Encontrados {len(job_links)} links de vagas. Extraindo detalhes de todas (em lotes).")
                    batch_size = settings.get("pipeline.job_batch_size", 5)
                    aba_semaforo = asyncio.Semaphore(5)

                    async def extrair_vaga_seguro(j_url):
                        async with aba_semaforo:
                            try:
                                vaga_html = await navegador.fetch_content(j_url, fast_mode=True)
                                texto_limpo_vaga = self.processor._clean_html_soup(vaga_html)
                                return f"URL: {j_url}\n{texto_limpo_vaga}"
                            except Exception as e:
                                logger.error(f"Erro ao extrair link de vaga {j_url}: {e}")
                                return None

                    for i in range(0, len(job_links), batch_size):
                        lote_links = job_links[i:i+batch_size]
                        logger.info(f"[{indice_at}/{total}] Baixando HTML do lote {i//batch_size + 1} ({len(lote_links)} vagas) concorrentemente...")
                        
                        resultados_html = await asyncio.gather(*[extrair_vaga_seguro(u) for u in lote_links])
                        textos_vagas = [res for res in resultados_html if res]
                        
                        texto_final = "\n\n=== NOVA VAGA ===\n\n".join(textos_vagas)
                        
                        try:
                            dados_estru = await self.processor.process(texto_final, self.schema)
                            if dados_estru and getattr(dados_estru, 'vagas', []):
                                lista_itens = dados_estru.vagas
                                logger.info(f"[{indice_at}/{total}] Lote {i//batch_size + 1} processado: {len(lista_itens)} itens.")
                                for item in lista_itens:
                                    await self._process_item(item, url)
                            else:
                                logger.warning(f"[{indice_at}/{total}] Nenhum item identificado no lote {i//batch_size + 1}.")
                        except ValidationError as ve:
                            logger.error(f"[{indice_at}/{total}] IA retornou formato inválido no lote {i//batch_size + 1}: {ve}")
                        except Exception as e:
                            logger.error(f"[{indice_at}/{total}] IA falhou ao estruturar o lote {i//batch_size + 1}: {e}")
                else:
                    texto_final = texto_bruto
                    try:
                        dados_estru = await self.processor.process(texto_final, self.schema)
                        if not dados_estru or not getattr(dados_estru, 'vagas', []):
                            logger.warning(f"[{indice_at}/{total}] Nenhum item identificado: {url}")
                            return

                        lista_itens = dados_estru.vagas
                        logger.info(f"[{indice_at}/{total}] Sucesso: {len(lista_itens)} itens de {url}")
                        for item in lista_itens:
                            await self._process_item(item, url)
                    except ValidationError as ve:
                        logger.error(f"[{indice_at}/{total}] Validação de dados falhou: {ve}")
                        return
                    
            except PlaywrightTimeoutError:
                logger.error(f"[{indice_at}/{total}] Timeout do navegador na URL: {url}")
            except Exception as e:
                logger.error(f"[{indice_at}/{total}] Erro inesperado na tarefa principal da URL: {e}")

    async def run(self):
        self._preparar_ambiente()
        lista_urls = self._load_urls()
        
        logger.info("=" * 40)
        num_trabalhadores = settings.get("pipeline.max_workers", 3)
        logger.info(f"AI-DE-S | MODO: JOBS | URLS: {len(lista_urls)} | PARALELISMO: {num_trabalhadores}")
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
        chave_item = f"{item.titulo.lower()}|{item.empresa.lower()}"

        async with self._trava:
            if chave_item in self.itens_vistos:
                logger.debug(f"Duplicata ignorada: {chave_item}")
                return
            self.itens_vistos.add(chave_item)

        if not item.titulo or not item.titulo.strip() or not item.empresa or not item.empresa.strip():
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
                await asyncio.to_thread(exportador.save, item, "jobs")
            except Exception as e:
                logger.error(f"Erro no exportador {exportador.__class__.__name__}: {e}")

