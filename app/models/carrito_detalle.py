from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base

class CarritoDetalle(Base):
    __tablename__ = "carrito_detalle"

    id = Column(Integer, primary_key=True, index=True)
    carrito_id = Column(Integer, ForeignKey("carritos.id"), nullable=False)
    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=False)
    cantidad = Column(Integer, nullable=False)

    carrito = relationship("Carrito", back_populates="detalle")
    producto = relationship("Producto")