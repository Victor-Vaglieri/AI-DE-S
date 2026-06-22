from app.schemas.jobs import JobListing, JobList

def test_job_listing_defaults():
    job = JobListing()
    assert job.titulo == "Título não encontrado"
    assert job.empresa == "Empresa não informada"
    assert job.localizacao == "Remoto/Não informado"
    assert job.salario == "Não informado"
    assert job.requisitos == []

def test_job_list_empty():
    job_list = JobList()
    assert job_list.vagas == []

