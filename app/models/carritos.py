from sqlalchemy import Column, Integer, DateTime, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

class Carrito(Base):
    __tablename__ = "carritos"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    fecha_creacion = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    estado = Column(String, default="activo")  # activo, abandonado, convertido a orden

    usuario = relationship("Usuario", back_populates="carritos")
    detalle = relationship("CarritoDetalle", back_populates="carrito")