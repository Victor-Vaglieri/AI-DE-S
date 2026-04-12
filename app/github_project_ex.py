import os
import requests
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class GitHubProjectExporter:
    
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.project_id = os.getenv("PROJECT_ID")
        self.repository_id = os.getenv("REPOSITORY_ID")
        self.url = "https://api.github.com/graphql"
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self._existing_titles_cache = set()
        self._is_cache_loaded = False

    def _execute_graphql(self, query, variables=None):
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

    def _mirror_locally(self, title, body):
        from datetime import datetime
        log_path = "data/github_history.log"
        os.makedirs("data", exist_ok=True)
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*60}\n")
                f.write(f"DATA: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write(f"TITULO: {title}\n")
                f.write(f"CONTEUDO:\n{body}\n")
                f.write(f"{'='*60}\n")
        except Exception as e:
            logging.error(f"Erro ao salvar espelho local: {e}")

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

        from datetime import datetime
        body = (
            f"### Detalhes da Vaga\n\n"
            f"- **Empresa:** {job.empresa}\n"
            f"- **Local:** {job.localizacao}\n"
            f"- **Salário:** {job.salario}\n"
            f"- **Link de Inscrição:** {job.link_inscricao}\n"
            f"- **Origem:** {job.origem}\n\n"
            f"### Requisitos & Stack\n\n"
            + ("\n".join([f"- {req}" for req in job.requisitos]) if job.requisitos else "Não informado")
            + f"\n\n---\n*Extraído automaticamente em {datetime.now().strftime('%d/%m/%Y %H:%M')}*"
        )

        # Se não houver REPOSITORY_ID, caímos de volta para DraftIssue ou erro
        if not self.repository_id:
            logging.warning("REPOSITORY_ID não configurado. Criando como rascunho (Draft)...")
            mutation = """
            mutation($project: ID!, $title: String!, $body: String!) {
              addProjectV2DraftIssue(input: {projectId: $project, title: $title, body: $body}) {
                projectItem { id }
              }
            }
            """
            result = self._execute_graphql(mutation, {"project": self.project_id, "title": target_title, "body": body})
        else:
            # 1. Criar a Issue real no repositório
            create_issue_mutation = """
            mutation($repoId: ID!, $title: String!, $body: String!) {
              createIssue(input: {repositoryId: $repoId, title: $title, body: $body}) {
                issue { id }
              }
            }
            """
            issue_data = self._execute_graphql(create_issue_mutation, {"repoId": self.repository_id, "title": target_title, "body": body})
            
            if issue_data and "createIssue" in issue_data:
                issue_id = issue_data["createIssue"]["issue"]["id"]
                
                # 2. Adicionar a Issue ao ProjectV2
                add_to_project_mutation = """
                mutation($project: ID!, $contentId: ID!) {
                  addProjectV2ItemById(input: {projectId: $project, contentId: $contentId}) {
                    item { id }
                  }
                }
                """
                result = self._execute_graphql(add_to_project_mutation, {"project": self.project_id, "contentId": issue_id})
            else:
                logging.error(f"Falha ao criar Issue real para: {target_title}")
                result = None

        if result:
            logging.info(f"Sucesso: {target_title}")
            self._existing_titles_cache.add(target_title)
            self._mirror_locally(target_title, body)