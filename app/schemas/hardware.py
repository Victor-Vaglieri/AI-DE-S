from pydantic import BaseModel, Field
from typing import List, Optional

class HardwarePrice(BaseModel):
    produto: str
    marca: str
    preco_vista: float
    preco_parcelado: Optional[float]
    loja: str
    em_estoque: bool

class HardwareList(BaseModel):
    produtos: List[HardwarePrice] = Field(description="Lista de todos os produtos encontrados na página")