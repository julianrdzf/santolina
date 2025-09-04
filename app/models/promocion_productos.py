from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base

class PromocionProducto(Base):
    __tablename__ = "promociones_productos"

    id = Column(Integer, primary_key=True, index=True)
    id_promocion = Column(Integer, ForeignKey("promociones.id"), nullable=False)
    id_producto = Column(Integer, ForeignKey("productos.id"), nullable=False)

    promocion = relationship("Promocion", back_populates="productos")
    # Se asume que en Producto se agregará:
    # promociones = relationship("PromocionProducto", back_populates="producto")