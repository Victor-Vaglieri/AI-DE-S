import os
import requests
import logging
import threading
from app.exporters_base import BaseExporter

logger = logging.getLogger("AI-DE-S.GitHub")

class GitHubProjectExporter(BaseExporter):
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.project_id = os.getenv("PROJECT_ID")
        self.repository_id = os.getenv("REPOSITORY_ID")
        self.url = "https://api.github.com/graphql"
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        self.cache_vistos = set()
        self.foi_carreg = False
        self._trava = threading.Lock()

    def _execute(self, query, vars=None):
        try:
            respo_post = requests.post(self.url, json={'query': query, 'variables': vars}, headers=self.headers, timeout=10)
            respo_post.raise_for_status()
            dados_json = respo_post.json()
            if "errors" in dados_json:
                logger.error(f"Erro GraphQL: {dados_json['errors'][0]['message']}")
                return None
            return dados_json.get("data")
        except Exception as e:
            logger.error(f"Erro conexão GitHub: {e}")
            return None

    def _load_cache(self):
        with self._trava:
            if self.foi_carreg: return
            if not self.token or not self.project_id: return
            
            consu_graph = """query($id: ID!) { node(id: $id) { ... on ProjectV2 { items(first: 100) { nodes { content { ... on DraftIssue { title } ... on Issue { title } } } } } } }"""
            retor_data = self._execute(consu_graph, {"id": self.project_id})
            if retor_data and "node" in retor_data:
                self.cache_vistos = {n["content"]["title"] for n in retor_data["node"]["items"]["nodes"] if n.get("content")}
                self.foi_carreg = True
                logger.info(f"Cache GitHub carregado: {len(self.cache_vistos)} itens.")

    def save(self, data, mode):
        if mode != "jobs": return
        if not self.foi_carreg: self._load_cache()

        titul_vaga = f"[{data.origem}] {data.titulo} @ {data.empresa}"
        
        with self._trava:
            if titul_vaga in self.cache_vistos: return

        corpo_vaga = f"Empresa: {data.empresa}\nLocal: {data.localizacao}\nLink: {data.link_inscricao}"
        
        if not self.repository_id:
            mutac_graph = """mutation($p: ID!, $t: String!, $b: String!) { addProjectV2DraftIssue(input: {projectId: $p, title: $t, body: $b}) { projectItem { id } } }"""
            respo_ia = self._execute(mutac_graph, {"p": self.project_id, "t": titul_vaga, "b": corpo_vaga})
        else:
            respo_ia = True 

        if respo_ia:
            logger.info(f"Enviado ao GitHub Project: {titul_vaga}")
            with self._trava:
                self.cache_vistos.add(titul_vaga)
