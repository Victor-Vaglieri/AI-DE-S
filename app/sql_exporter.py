import logging
import threading
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.exporters_base import BaseExporter
from app.models import Base, JobModel, HardwareModel

logger = logging.getLogger("AI-DE-S.SQL")

class SqlExporter(BaseExporter):
    _lock = threading.Lock()

    def __init__(self, db_url="sqlite:///data/ai_des.db"):
        self.db_url = db_url
    
        connect_args = {}
        if self.db_url.startswith("sqlite"):
            connect_args = {"timeout": 30}

        motor_banco = create_engine(self.db_url, connect_args=connect_args)
        
        if self.db_url.startswith("sqlite"):
            @event.listens_for(motor_banco, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.close()

        Base.metadata.create_all(motor_banco)
        self.Sessao = sessionmaker(bind=motor_banco)

    def save(self, data, mode):
        with self._lock:
            sessao_atual = self.Sessao()
            try:
                if mode == "jobs":
                    dados_vaga = data.model_dump()
                    dados_vaga['requisitos'] = ", ".join(dados_vaga.get('requisitos', []))
                    sessao_atual.add(JobModel(**dados_vaga))
                elif mode == "hardware":
                    sessao_atual.add(HardwareModel(**data.model_dump()))
                sessao_atual.commit()
                logger.debug(f"SQL: Item salvo no banco ({mode})")
            except Exception as e:
                sessao_atual.rollback()
                logger.error(f"Erro SQL: {e}")
            finally:
                sessao_atual.close()
