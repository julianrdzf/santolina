from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from app.db import Base
from datetime import datetime

class Evento(Base):
    __tablename__ = "eventos"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, nullable=False)
    descripcion = Column(String)
    categoria_id = Column(Integer, ForeignKey("categorias_eventos.id"), nullable=True)
    categoria = relationship("CategoriaEvento", back_populates="eventos")
    ubicacion = Column(String, nullable=True)
    direccion = Column(String, nullable=True)
    costo = Column(Numeric(10, 2), nullable=True)
    costo_dolares = Column(Numeric(10, 2), nullable=True)  # Precio en USD para PayPal
    imagen = Column(String, nullable=True)  # URL de la imagen del evento
    imagen_public_id = Column(String, nullable=True)  # public_id de la imagen del evento
    prioridad = Column(Integer, nullable=True)  # Prioridad para ordenar eventos (menor = mayor prioridad)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Nuevas relaciones
    fechas_evento = relationship("FechaEvento", back_populates="evento", order_by="FechaEvento.fecha")