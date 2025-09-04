from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base

class CategoriaProducto(Base):
    __tablename__ = "categorias_productos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    id_categoria_padre = Column(Integer, ForeignKey("categorias_productos.id"), nullable=True)

    subcategorias = relationship("CategoriaProducto", backref="categoria_padre", remote_side=[id])
    productos = relationship("Producto", back_populates="categoria")