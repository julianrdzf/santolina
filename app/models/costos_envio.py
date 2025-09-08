from sqlalchemy import Column, Integer, Float, String, Boolean
from app.db import Base

class CostoEnvio(Base):
    __tablename__ = "costos_envio"

    id = Column(Integer, primary_key=True, index=True)
    departamento = Column(String, unique=True, nullable=False, index=True)
    costo = Column(Float, nullable=False, default=0)
    activo = Column(Boolean, default=True)  # Para poder desactivar temporalmente
