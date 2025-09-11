from pydantic import BaseModel
from datetime import date
from typing import List, Optional

class FechaEventoCreate(BaseModel):
    evento_id: int
    fecha: date

class FechaEventoOut(BaseModel):
    id: int
    evento_id: int
    fecha: date
    horarios: Optional[List["HorarioFechaEventoOut"]] = []

    class Config:
        orm_mode = True

# Import needed for forward reference
from app.schemas.horario_fecha_evento import HorarioFechaEventoOut
FechaEventoOut.model_rebuild()
