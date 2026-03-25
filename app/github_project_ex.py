import os
import requests
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class GitHubProjectExporter:
    
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.project_id = os.getenv("PROJECT_ID")
        self.url = "https://api.github.com/graphql"
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self._existing_titles_cache = set()
        self._is_cache_loaded = False

    def _execute_graphql(self, query, variables=None):
        """Método utilitário para chamadas GraphQL com tratamento de erro."""
        try:
            response = requests.post(
                self.url, 
                json={'query': query, 'variables': variables}, 
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            res_json = response.json()
            
            if "errors" in res_json:
                logging.error(f"Erro GraphQL: {res_json['errors']}")
                return None
            return res_json.get("data")
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro de conexão: {e}")
            return None

    def _load_existing_items(self):
        query = """
        query($project: ID!) {
          node(id: $project) {
            ... on ProjectV2 {
              items(first: 100) {
                nodes {
                  content {
                    ... on DraftIssue { title }
                    ... on Issue { title }
                  }
                }
              }
            }
          }
        }
        """
        data = self._execute_graphql(query, {"project": self.project_id})
        if data and "node" in data:
            nodes = data["node"]["items"]["nodes"]
            self._existing_titles_cache = {
                n["content"]["title"] for n in nodes 
                if n.get("content") and "title" in n["content"]
            }
            self._is_cache_loaded = True
            logging.info(f"Cache carregado: {len(self._existing_titles_cache)} itens encontrados.")

    def save(self, data, mode):
        if mode != "jobs":
            return
        
        if not self._is_cache_loaded:
            self._load_existing_items()

        job = data 
        
        try:
            target_title = f"[{job.origem}] {job.titulo} @ {job.empresa}"
        except AttributeError:
            logging.error("Exportador recebeu objeto inválido. Esperado JobListing.")
            return

        if target_title in self._existing_titles_cache:
            logging.info(f"Ignorado (já existe no GitHub): {target_title}")
            return

        body = (
            f"**Local:** {job.localizacao}\n"
            f"**Salário:** {job.salario}\n"
            f"**Requisitos:** {', '.join(job.requisitos) if job.requisitos else 'Não informado'}\n"
            f"**Link:** {job.link_inscricao}"
        )

        variables = {
            "project": self.project_id,
            "title": target_title,
            "body": body
        }

        mutation = """
        mutation($project: ID!, $title: String!, $body: String!) {
          addProjectV2DraftIssue(input: {projectId: $project, title: $title, body: $body}) {
            projectItem { id }
          }
        }
        """

        result = self._execute_graphql(mutation, variables)
        if result:
            logging.info(f"Sucesso: {target_title}")
            self._existing_titles_cache.add(target_title)