import pytest
from unittest.mock import patch
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import inspect
from app.sql_exporter import SqlExporter
from app.schemas.jobs import JobListing
from app.models import JobModel, Base

@pytest.fixture
def sqlite_memory_exporter():
    exporter = SqlExporter(db_url="sqlite:///:memory:")
    yield exporter
    # Limpeza após o teste
    Base.metadata.drop_all(exporter.db_engine)

def test_sql_exporter_initialization(sqlite_memory_exporter):
    assert sqlite_memory_exporter.db_engine is not None
    
    inspector = inspect(sqlite_memory_exporter.db_engine)
    assert 'jobs' in inspector.get_table_names()

def test_sql_exporter_save_job(sqlite_memory_exporter):
    job_data = JobListing(
        titulo="Software Engineer",
        empresa="Tech Innovators",
        localizacao="Remote",
        origem="LinkedIn",
        salario="10k - 15k",
        requisitos=["Python", "FastAPI", "SQL"],
        link_inscricao="https://example.com/apply"
    )

    sqlite_memory_exporter.save(job_data, mode="jobs")

    session = sqlite_memory_exporter.Session()
    saved_job = session.query(JobModel).first()
    
    assert saved_job is not None
    assert saved_job.titulo == "Software Engineer"
    assert saved_job.empresa == "Tech Innovators"
    assert saved_job.origem == "LinkedIn"
    assert saved_job.salario == "10k - 15k"
    assert saved_job.link_inscricao == "https://example.com/apply"
    
    assert saved_job.requisitos == "Python, FastAPI, SQL"
    
    session.close()

def test_sql_exporter_rollback_on_error(sqlite_memory_exporter, caplog):
    job_data = JobListing(
        titulo="Faulty Job",
        empresa="Crash Corp",
        localizacao="Remote",
        origem="Web",
        salario="Não informado",
        requisitos=[],
        link_inscricao="http://error.com"
    )

    with patch("sqlalchemy.orm.Session.commit", side_effect=SQLAlchemyError("Erro Simulado de DB")):
        sqlite_memory_exporter.save(job_data, mode="jobs")

    assert "Erro SQL: Erro Simulado de DB" in caplog.text
    
    session = sqlite_memory_exporter.Session()
    assert session.query(JobModel).count() == 0
    session.close()
