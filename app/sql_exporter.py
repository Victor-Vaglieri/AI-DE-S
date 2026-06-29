import logging
import threading
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from app.exporters_base import BaseExporter
from app.models import Base, JobModel

logger = logging.getLogger("AI-DE-S.SQL")

class SqlExporter(BaseExporter):
    _lock = threading.Lock()

    def __init__(self, db_url="sqlite:///data/ai_des.db"):
        self.db_url = db_url
    
        connect_args = {}
        if self.db_url.startswith("sqlite"):
            connect_args = {"timeout": 30}

        self.db_engine = create_engine(self.db_url, connect_args=connect_args)
        
        if self.db_url.startswith("sqlite"):
            @event.listens_for(self.db_engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.close()

        Base.metadata.create_all(self.db_engine)
        self.Session = sessionmaker(bind=self.db_engine)

    def save(self, data, mode):
        with self._lock:
            session = self.Session()
            try:
                job_data = data.model_dump()
                job_data['requisitos'] = ", ".join(job_data.get('requisitos', []))
                session.add(JobModel(**job_data))
                session.commit()
                logger.debug("SQL: Vaga salva no banco")
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Erro SQL: {e}")
            except Exception as e:
                session.rollback()
                logger.error(f"Erro Inesperado: {e}")
            finally:
                session.close()
