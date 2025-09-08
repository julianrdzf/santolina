from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base

class CategoriaProducto(Base):
    __tablename__ = "categorias_productos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    id_categoria_padre = Column(Integer, ForeignKey("categorias_productos.id"), nullable=True)

    # Relación hacia subcategorías
    subcategorias = relationship(
        "CategoriaProducto",
        back_populates="categoria_padre",
        cascade="all, delete"
    )

    # Relación hacia la categoría padre
    categoria_padre = relationship(
        "CategoriaProducto",
        remote_side=[id],
        back_populates="subcategorias"
    )

    productos = relationship("Producto", back_populates="categoria")