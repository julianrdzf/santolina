from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

class CompraEbook(Base):
    __tablename__ = "compra_ebooks"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    ebook_id = Column(Integer, ForeignKey("ebooks.id"), nullable=False)
    fecha_compra = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    precio_pagado = Column(Float, nullable=False)  # Precio al momento de la compra
    metodo_pago = Column(String, nullable=True)    # mercadopago, paypal, etc.
    estado_pago = Column(String, default="pendiente")  # pendiente, pagado, fallido
    transaction_id = Column(String, nullable=True)  # ID de la transacción del proveedor de pago
    codigo_descarga = Column(String, nullable=True, unique=True)  # Código único para descargar
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="compras_ebooks")
    ebook = relationship("Ebook", back_populates="compras")
