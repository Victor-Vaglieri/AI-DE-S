import os
import yaml
import logging

logger = logging.getLogger("AI-DE-S.Settings")

class Settings:
    def __init__(self, config_path="config/settings.yaml"):
        self.config_path = config_path
        self.data = self._load_config()

    def _load_config(self):
        if not os.path.exists(self.config_path):
            logger.warning(f"Usando padroes. Arquivo não encontrado: {self.config_path}")
            return {}
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar {self.config_path}: {e}")
            return {}

    def get(self, key_path, default=None):
        keys = key_path.split('.')
        value = self.data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

settings = Settings()
