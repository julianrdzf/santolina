from sqlalchemy import Column, Integer, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base

class FechaEvento(Base):
    __tablename__ = "fechas_evento"

    id = Column(Integer, primary_key=True, index=True)
    evento_id = Column(Integer, ForeignKey("eventos.id"), nullable=False)
    fecha = Column(Date, nullable=False)

    # Relaciones
    evento = relationship("Evento", back_populates="fechas_evento")
    horarios = relationship("HorarioFechaEvento", back_populates="fecha_evento", order_by="HorarioFechaEvento.hora_inicio")
