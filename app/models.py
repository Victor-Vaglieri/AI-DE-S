from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class JobModel(Base):
    __tablename__ = 'jobs'
    
    id = Column(Integer, primary_key=True)
    titulo = Column(String(255))
    empresa = Column(String(255))
    localizacao = Column(String(255))
    origem = Column(String(100))
    salario = Column(String(100))
    requisitos = Column(Text)
    link_inscricao = Column(String(500))
    extraido_em = Column(DateTime, default=datetime.now)
