from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.db import Base
from datetime import datetime, timezone

class Promocion(Base):
    __tablename__ = "promociones"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, nullable=False)
    descripcion = Column(String, nullable=True)
    tipo_descuento = Column(String, nullable=False)  # "porcentaje" o "fijo"
    valor = Column(Float, nullable=False)
    fecha_inicio = Column(DateTime, nullable=False)
    fecha_fin = Column(DateTime, nullable=False)
    activo = Column(Boolean, default=True)

    productos = relationship("PromocionProducto", back_populates="promocion")