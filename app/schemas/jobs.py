from pydantic import BaseModel, Field
from typing import List, Optional

class JobListing(BaseModel):
    titulo: str = Field(default="Título não encontrado", description="O nome do cargo ou posição")
    empresa: str = Field(default="Empresa não informada", description="Nome da empresa contratante")
    localizacao: str = Field(default="Remoto/Não informado", description="Cidade, estado ou se é Remoto")
    origem: str = Field(default="Plataforma não identificada", description="Plataforma de origem da vaga")
    salario: Optional[str] = Field(default="Não informado", description="Faixa salarial se mencionada")
    requisitos: List[str] = Field(default_factory=list, description="Tecnologias ou habilidades")
    link_inscricao: Optional[str] = Field(default="", description="URL direta da vaga")

class JobList(BaseModel):
    vagas: List[JobListing] = Field(default_factory=list, description="Lista de todas as oportunidades")