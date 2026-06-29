from abc import ABC, abstractmethod
from typing import Any

class BaseExporter(ABC):
    @abstractmethod
    def save(self, data: Any, mode: str) -> Any:
        pass
