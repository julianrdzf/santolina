from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID

class Reserva(Base):
    __tablename__ = "reservas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    email = Column(String, nullable=False)
    celular = Column(String, nullable=True)
    evento_id = Column(Integer, ForeignKey("eventos.id"), nullable=False)
    cupos = Column(Integer, nullable=False)
    fecha_creacion = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    estado_pago = Column(String, default="pendiente", nullable=False)

    evento = relationship("Evento", back_populates="reservas")
    usuario = relationship("Usuario", back_populates="reservas")