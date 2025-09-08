from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base
from app.models.imagenes_productos import ImagenProducto
from app.models.promocion_productos import PromocionProducto
from app.models.promociones import Promocion

class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String, nullable=True)
    precio = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False)
    id_categoria = Column(Integer, ForeignKey("categorias_productos.id"), nullable=True)

    categoria = relationship("CategoriaProducto", back_populates="productos")
    imagenes = relationship("ImagenProducto", back_populates="producto")
    promociones = relationship("PromocionProducto", back_populates="producto")