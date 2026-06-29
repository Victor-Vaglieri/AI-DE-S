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
        
        self.seen_cache = set()
        self.is_loaded = False
        self._lock = threading.Lock()

    def _execute(self, query, variables=None):
        try:
            response = requests.post(
                self.url, 
                json={'query': query, 'variables': variables}, 
                headers=self.headers, 
                timeout=10
            )
            response.raise_for_status()
            json_data = response.json()
            if "errors" in json_data:
                logger.error(f"Erro GraphQL: {json_data['errors'][0]['message']}")
                return None
            return json_data.get("data")
        except Exception as e:
            logger.error(f"Erro conexão GitHub: {e}")
            return None

    def _load_cache(self):
        with self._lock:
            if self.is_loaded: 
                return
            if not self.token or not self.project_id: 
                return
            
            has_next = True
            cursor = None
            
            while has_next:
                cursor_arg = f', after: "{cursor}"' if cursor else ""
                graphql_query = f"""
                query($id: ID!) {{ 
                    node(id: $id) {{ 
                        ... on ProjectV2 {{ 
                            items(last: 200{cursor_arg}) {{ 
                                pageInfo {{ hasNextPage endCursor }}
                                nodes {{ 
                                    content {{ ... on DraftIssue {{ title }} ... on Issue {{ title }} }} 
                                }} 
                            }} 
                        }} 
                    }} 
                }}
                """
                return_data = self._execute(graphql_query, {"id": self.project_id})
                
                if return_data and "node" in return_data and return_data["node"].get("items"):
                    items_data = return_data["node"]["items"]
                    for node in items_data["nodes"]:
                        if node and node.get("content") and node["content"].get("title"):
                            self.seen_cache.add(node["content"]["title"].lower().strip())
                    
                    has_next = items_data["pageInfo"]["hasNextPage"]
                    cursor = items_data["pageInfo"]["endCursor"]
                else:
                    has_next = False
                    
            self.is_loaded = True
            logger.info(f"Cache GitHub carregado: {len(self.seen_cache)} itens totais paginados.")

    def save(self, data, mode):
        if mode != "jobs": 
            return
        
        if not self.is_loaded: 
            self._load_cache()

        job_title = f"[{data.origem}] {data.titulo} @ {data.empresa}"
        search_str = f"{data.titulo} @ {data.empresa}".lower().strip()
        
        with self._lock:
            for cached_title in self.seen_cache:
                if search_str in cached_title:
                    return
            
            self.seen_cache.add(job_title.lower().strip())

        job_body = f"Empresa: {data.empresa}\nLocal: {data.localizacao}\nLink: {data.link_inscricao}"
        
        if not self.repository_id:
            graphql_mutation = """
            mutation($p: ID!, $t: String!, $b: String!) { 
                addProjectV2DraftIssue(input: {projectId: $p, title: $t, body: $b}) { 
                    projectItem { id } 
                } 
            }
            """
            mutation_response = self._execute(graphql_mutation, {"p": self.project_id, "t": job_title, "b": job_body})
        else:
            # Placeholder for future repository issue creation
            mutation_response = True 

        if mutation_response:
            logger.info(f"Enviado ao GitHub Project: {job_title}")
