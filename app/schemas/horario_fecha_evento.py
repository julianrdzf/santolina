from pydantic import BaseModel
from datetime import time
from typing import Optional

class HorarioFechaEventoCreate(BaseModel):
    fecha_evento_id: int
    hora_inicio: time
    duracion_minutos: int
    cupos: int

class HorarioFechaEventoOut(BaseModel):
    id: int
    fecha_evento_id: int
    hora_inicio: time
    duracion_minutos: int
    cupos: int

    class Config:
        orm_mode = True
