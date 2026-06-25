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
            
            tem_mais = True
            cursor = None
            
            while tem_mais:
                cursor_arg = f', after: "{cursor}"' if cursor else ""
                consu_graph = f"""
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
                retor_data = self._execute(consu_graph, {"id": self.project_id})
                
                if retor_data and "node" in retor_data and retor_data["node"].get("items"):
                    items_data = retor_data["node"]["items"]
                    for n in items_data["nodes"]:
                        if n and n.get("content") and n["content"].get("title"):
                            self.cache_vistos.add(n["content"]["title"].lower().strip())
                    
                    tem_mais = items_data["pageInfo"]["hasNextPage"]
                    cursor = items_data["pageInfo"]["endCursor"]
                else:
                    tem_mais = False
                    
            self.foi_carreg = True
            logger.info(f"Cache GitHub carregado: {len(self.cache_vistos)} itens totais paginados.")

    def save(self, data, mode):
        if mode != "jobs": return
        if not self.foi_carreg: self._load_cache()

        titul_vaga = f"[{data.origem}] {data.titulo} @ {data.empresa}"
        busca_str = f"{data.titulo} @ {data.empresa}".lower().strip()
        
        with self._trava:
            for cached_title in self.cache_vistos:
                if busca_str in cached_title:
                    return
            
            self.cache_vistos.add(titul_vaga.lower().strip())

        corpo_vaga = f"Empresa: {data.empresa}\nLocal: {data.localizacao}\nLink: {data.link_inscricao}"
        
        if not self.repository_id:
            mutac_graph = """mutation($p: ID!, $t: String!, $b: String!) { addProjectV2DraftIssue(input: {projectId: $p, title: $t, body: $b}) { projectItem { id } } }"""
            respo_ia = self._execute(mutac_graph, {"p": self.project_id, "t": titul_vaga, "b": corpo_vaga})
        else:
            respo_ia = True 

        if respo_ia:
            logger.info(f"Enviado ao GitHub Project: {titul_vaga}")
