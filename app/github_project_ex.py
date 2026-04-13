import os
import requests
import logging
from app.exporters_base import BaseExporter

logger = logging.getLogger("AI-DE-S.GitHub")

class GitHubProjectExporter(BaseExporter):
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.project_id = os.getenv("PROJECT_ID")
        self.repository_id = os.getenv("REPOSITORY_ID")
        self.url = "https://api.github.com/graphql"
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self._cache = set()
        self._loaded = False

    def _execute(self, query, vars=None):
        try:
            res = requests.post(self.url, json={'query': query, 'variables': vars}, headers=self.headers, timeout=10)
            res.raise_for_status()
            data = res.json()
            if "errors" in data:
                logger.error(f"Erro GraphQL: {data['errors'][0]['message']}")
                return None
            return data.get("data")
        except Exception as e:
            logger.error(f"Erro conexao GitHub: {e}")
            return None

    def _load_cache(self):
        if not self.token or not self.project_id: return
        query = """query($id: ID!) { node(id: $id) { ... on ProjectV2 { items(first: 100) { nodes { content { ... on DraftIssue { title } ... on Issue { title } } } } } } }"""
        data = self._execute(query, {"id": self.project_id})
        if data and "node" in data:
            self._cache = {n["content"]["title"] for n in data["node"]["items"]["nodes"] if n.get("content")}
            self._loaded = True
            logger.info(f"Cache GitHub: {len(self._cache)} itens.")

    def save(self, data, mode):
        if mode != "jobs": return
        if not self._loaded: self._load_cache()

        title = f"[{data.origem}] {data.titulo} @ {data.empresa}"
        if title in self._cache: return

        body = f"Empresa: {data.empresa}\nLocal: {data.localizacao}\nLink: {data.link_inscricao}"
        
        if not self.repository_id:
            mutation = """mutation($p: ID!, $t: String!, $b: String!) { addProjectV2DraftIssue(input: {projectId: $p, title: $t, body: $b}) { projectItem { id } } }"""
            res = self._execute(mutation, {"p": self.project_id, "t": title, "b": body})
        else:
            res = True 

        if res:
            logger.info(f"GitHub: {title}")
            self._cache.add(title)
