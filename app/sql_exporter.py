import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.exporters_base import BaseExporter
from app.models import Base, JobModel, HardwareModel

logger = logging.getLogger("AI-DE-S.SQL")

class SqlExporter(BaseExporter):
    def __init__(self, db_url="sqlite:///data/ai_des.db"):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def save(self, data, mode):
        session = self.Session()
        try:
            if mode == "jobs":
                job_data = data.model_dump()
                job_data['requisitos'] = ", ".join(job_data.get('requisitos', []))
                session.add(JobModel(**job_data))
            elif mode == "hardware":
                session.add(HardwareModel(**data.model_dump()))
            session.commit()
            logger.info(f"DB Salvo: {mode}")
        except Exception as e:
            session.rollback()
            logger.error(f"Erro DB: {e}")
        finally:
            session.close()
