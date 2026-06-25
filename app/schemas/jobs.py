from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

class JobListing(BaseModel):
    titulo: str = Field(description="O nome do cargo ou posição")
    empresa: str = Field(description="Nome da empresa contratante")
    localizacao: str = Field(description="Cidade, estado ou se é Remoto")
    origem: str = Field(description="Plataforma de origem da vaga, ex: LinkedIn, Gupy")
    salario: str = Field(description="Faixa salarial se mencionada, ou 'Não informado'")
    requisitos: List[str] = Field(description="Tecnologias ou habilidades")
    link_inscricao: str = Field(description="URL direta da vaga, ou vazio caso não encontre")

    @field_validator('requisitos', mode='before')
    @classmethod
    def validate_requisitos(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        return v

class JobList(BaseModel):
    vagas: List[JobListing] = Field(description="Lista de todas as oportunidades")