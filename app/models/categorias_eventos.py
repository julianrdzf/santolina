from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base

class CategoriaEvento(Base):
    __tablename__ = "categorias_eventos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    id_categoria_padre = Column(Integer, ForeignKey("categorias_eventos.id"), nullable=True)

    # Relación hacia subcategorías
    subcategorias = relationship(
        "CategoriaEvento",
        back_populates="categoria_padre",
        cascade="all, delete"
    )

    # Relación hacia la categoría padre
    categoria_padre = relationship(
        "CategoriaEvento",
        remote_side=[id],
        back_populates="subcategorias"
    )
    
    # Relación con eventos
    eventos = relationship("Evento", back_populates="categoria")
