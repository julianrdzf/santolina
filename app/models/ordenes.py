from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

class Orden(Base):
    __tablename__ = "ordenes"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    fecha = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    total = Column(Float, nullable=False)
    estado = Column(String, default="pendiente")  # pendiente, pagado, enviado, cancelado
    direccion_envio_id = Column(Integer, ForeignKey("direcciones.id"), nullable=True)
    metodo_envio_id = Column(Integer, ForeignKey("costos_envio.id"), nullable=False)
    metodo_pago = Column(String, nullable=True)
    descuento_total = Column(Float, default=0)
    costo_envio = Column(Float, default=0)
    total_final = Column(Float, nullable=False)
    transaction_id = Column(String, nullable=True)  # ID de la transacción del proveedor de pago

    usuario = relationship("Usuario", back_populates="ordenes")
    direccion_envio = relationship("Direccion")
    metodo_envio = relationship("CostoEnvio")
    detalle = relationship("OrdenDetalle", back_populates="orden")