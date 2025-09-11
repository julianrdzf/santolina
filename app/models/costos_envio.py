from sqlalchemy import Column, Integer, Float, String, Boolean
from app.db import Base

class CostoEnvio(Base):
    __tablename__ = "costos_envio"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False, index=True)
    descripcion = Column(String, nullable=True)
    costo = Column(Float, nullable=False, default=0)
    url_imagen = Column(String, nullable=True)  # Para mapas de zona de envío a futuro
    activo = Column(Boolean, default=True)
    requiere_direccion = Column(Boolean, default=True)  # False para retiros
