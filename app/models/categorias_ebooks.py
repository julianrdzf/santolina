from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base

class CategoriaEbook(Base):
    __tablename__ = "categorias_ebooks"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    id_categoria_padre = Column(Integer, ForeignKey("categorias_ebooks.id"), nullable=True)

    # Relación hacia subcategorías
    subcategorias = relationship(
        "CategoriaEbook",
        back_populates="categoria_padre",
        cascade="all, delete"
    )

    # Relación hacia la categoría padre
    categoria_padre = relationship(
        "CategoriaEbook",
        remote_side=[id],
        back_populates="subcategorias"
    )

    ebooks = relationship("Ebook", back_populates="categoria")
