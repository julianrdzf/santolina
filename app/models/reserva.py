from sqlalchemy import Column, Integer, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from app.db import Base
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID

class Reserva(Base):
    __tablename__ = "reservas"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    horario_id = Column(Integer, ForeignKey("horarios_fecha_evento.id"), nullable=False)
    fecha_creacion = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    cupos = Column(Integer, nullable=False)
    estado_pago = Column(String, default="pendiente", nullable=False)
    transaction_id = Column(String, nullable=True)  # ID de la transacción del proveedor de pago

    # Relaciones
    usuario = relationship("Usuario")
    horario = relationship("HorarioFechaEvento", back_populates="reservas")