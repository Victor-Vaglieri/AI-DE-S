from app.schemas.jobs import JobListing, JobList
from app.schemas.hardware import HardwarePrice, HardwareList

def test_job_listing_defaults():
    job = JobListing()
    assert job.titulo == "Título não encontrado"
    assert job.empresa == "Empresa não informada"
    assert job.localizacao == "Remoto/Não informado"
    assert job.salario == "Não informado"
    assert job.requisitos == []

def test_hardware_price_defaults():
    hw = HardwarePrice()
    assert hw.produto == "Não informado"
    assert hw.marca == "Desconhecida"
    assert hw.preco_vista == 0.0
    assert hw.em_estoque is False

def test_job_list_empty():
    job_list = JobList()
    assert job_list.vagas == []

def test_hardware_list_empty():
    hw_list = HardwareList()
    assert hw_list.produtos == []
