from abc import ABC, abstractmethod
from typing import Any

class BaseExporter(ABC):
    @abstractmethod
    def save(self, data: Any, mode: str) -> Any:
        """
        Salva os dados extraídos no destino específico.
        
        Args:
            data: Objeto Pydantic com os dados estruturados.
            mode: O nicho da extração (jobs, hardware, etc).
        """
        pass
