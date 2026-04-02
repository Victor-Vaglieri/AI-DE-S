from pydantic import BaseModel, Field
from typing import List, Optional

class HardwarePrice(BaseModel):
    produto: str = Field(default="Não informado", description="Nome completo do produto")
    marca: str = Field(default="Desconhecida", description="Marca do fabricante")
    preco_vista: float = Field(default=0.0, description="Preço à vista (boleto/PIX)")
    preco_parcelado: Optional[float] = Field(default=0.0, description="Preço total parcelado no cartão")
    loja: str = Field(default="Loja não identificada", description="Nome da loja que vende o produto")
    em_estoque: bool = Field(default=False, description="Se o produto está disponível para compra")

class HardwareList(BaseModel):
    produtos: List[HardwarePrice] = Field(default_factory=list, description="Lista de todos os produtos encontrados na página")