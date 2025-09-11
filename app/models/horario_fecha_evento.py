from sqlalchemy import Column, Integer, Time, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime, timedelta
from app.db import Base

class HorarioFechaEvento(Base):
    __tablename__ = "horarios_fecha_evento"

    id = Column(Integer, primary_key=True, index=True)
    fecha_evento_id = Column(Integer, ForeignKey("fechas_evento.id"), nullable=False)
    hora_inicio = Column(Time, nullable=False)
    duracion_minutos = Column(Integer, nullable=False)
    cupos = Column(Integer, nullable=False)

    # Relaciones
    fecha_evento = relationship("FechaEvento", back_populates="horarios")
    reservas = relationship("Reserva", back_populates="horario")
    
    @hybrid_property
    def hora_fin(self):
        """Calcula la hora de fin basada en hora_inicio + duracion_minutos"""
        if self.hora_inicio and self.duracion_minutos:
            # Convertir time a datetime para poder sumar timedelta
            dt = datetime.combine(datetime.today(), self.hora_inicio)
            dt_fin = dt + timedelta(minutes=self.duracion_minutos)
            return dt_fin.time()
        return None
