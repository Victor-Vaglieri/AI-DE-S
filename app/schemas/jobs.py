from pydantic import BaseModel, Field
from typing import List, Optional

class JobListing(BaseModel):
    titulo: str = Field(description="O nome do cargo ou posição")
    empresa: str = Field(description="Nome da empresa contratante")
    localizacao: str = Field(description="Cidade, estado ou se é Remoto")
    salario: Optional[str] = Field(description="Faixa salarial se mencionada, caso contrário 'Não informado'")
    requisitos: List[str] = Field(description="Lista de tecnologias ou habilidades exigidas")
    link_inscricao: Optional[str] = Field(description="URL para se candidatar")
class JobList(BaseModel):
    vagas: List[JobListing] = Field(description="Lista de todas as oportunidades de emprego encontradas na página")