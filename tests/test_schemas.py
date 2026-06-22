from app.schemas.jobs import JobListing, JobList

def test_job_listing_creation():
    job = JobListing(
        titulo="Engenheiro",
        empresa="Tech Corp",
        localizacao="Remoto",
        origem="Web",
        salario="10000",
        requisitos=["Python", "SQL"],
        link_inscricao="http://vaga.com"
    )
    assert job.titulo == "Engenheiro"
    assert job.empresa == "Tech Corp"
    assert job.requisitos == ["Python", "SQL"]

def test_job_list_creation():
    job_list = JobList(vagas=[])
    assert job_list.vagas == []

