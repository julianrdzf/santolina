from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db import Base
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

class CuponUso(Base):
    __tablename__ = "cupones_uso"

    id = Column(Integer, primary_key=True, index=True)
    cupon_id = Column(Integer, ForeignKey("cupones.id"), nullable=False)
    usuario_id = Column(PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    fecha_uso = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    cupon = relationship("Cupon", back_populates="usos")