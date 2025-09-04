from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base
from datetime import datetime, timezone

class Pago(Base):
    __tablename__ = "pagos"

    id = Column(Integer, primary_key=True, index=True)
    orden_id = Column(Integer, ForeignKey("ordenes.id"), nullable=False)
    monto = Column(Float, nullable=False)
    metodo = Column(String, nullable=False)  # tarjeta, PayPal, etc.
    estado = Column(String, default="pendiente")  # aprobado, rechazado, pendiente
    fecha = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    orden = relationship("Orden")