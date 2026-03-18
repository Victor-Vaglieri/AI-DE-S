from pydantic import BaseModel, Field
from typing import List, Optional

class JobListing(BaseModel):
    titulo: str = Field(description="O nome do cargo ou posição")
    empresa: str = Field(description="Nome da empresa contratante")
    localizacao: str = Field(description="Cidade, estado ou se é Remoto")
    origem: str = Field(description="Plataforma de origem da vaga (ex: LinkedIn, Gupy, Indeed)")
    salario: Optional[str] = Field(description="Faixa salarial se mencionada, caso contrário 'Não informado'")
    requisitos: List[str] = Field(description="Tecnologias ou habilidades visíveis na listagem")
    link_inscricao: str = Field(description="URL direta da vaga ou o link da página de listagem caso a específica não seja encontrada")

class JobList(BaseModel):
    vagas: List[JobListing] = Field(description="Lista de todas as oportunidades de emprego encontradas na página")