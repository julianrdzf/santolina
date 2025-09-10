from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from app.db import Base
from datetime import datetime

class Evento(Base):
    __tablename__ = "eventos"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, nullable=False)
    descripcion = Column(String)
    fecha = Column(Date, nullable=False)
    cupos_totales = Column(Integer, nullable=False)
    categoria_id = Column(Integer, ForeignKey("categorias_eventos.id"), nullable=True)
    categoria = relationship("CategoriaEvento", back_populates="eventos")
    hora = Column(String, nullable=True)       # Podrías usar Time si querés validación de hora
    ubicacion = Column(String, nullable=True)
    direccion = Column(String, nullable=True)
    costo = Column(Numeric(10, 2), nullable=True)
    imagen = Column(String, nullable=True)  # URL de la imagen del evento

    created_at = Column(DateTime, default=datetime.utcnow)

    reservas = relationship("Reserva", back_populates="evento")