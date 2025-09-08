from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

class Direccion(Base):
    __tablename__ = "direcciones"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    direccion = Column(String, nullable=False)  # calle, número, apto
    detalle = Column(String, nullable=True)     # información adicional, ej: esquina
    ciudad = Column(String, nullable=False)
    departamento = Column(String, nullable=True)
    codigo_postal = Column(String, nullable=True)
    pais = Column(String, nullable=False)
    tipo = Column(String, nullable=True)  # ej: casa, trabajo, etc.

    usuario = relationship("Usuario", back_populates="direcciones")