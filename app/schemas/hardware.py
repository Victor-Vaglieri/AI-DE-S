from pydantic import BaseModel, Field
from typing import Optional

class HardwarePrice(BaseModel):
    produto: str = Field(description="Nome completo do componente (ex: RTX 4060)")
    marca: str = Field(description="Fabricante do componente")
    preco_vista: float = Field(description="Preço para pagamento via PIX ou boleto")
    preco_parcelado: Optional[float] = Field(description="Preço total parcelado")
    loja: str = Field(description="Nome da loja vendedora")
    em_estoque: bool = Field(description="Verdadeiro se o botão de compra estiver ativo")