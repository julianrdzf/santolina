from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db import Base

class CategoriaEvento(Base):
    __tablename__ = "categorias_eventos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    
    # Relación con eventos
    eventos = relationship("Evento", back_populates="categoria")