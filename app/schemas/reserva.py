from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID

class ReservaCreate(BaseModel):
    usuario_id: UUID
    horario_id: int
    cupos: int
    estado_pago: Optional[str] = "pendiente"

class ReservaOut(BaseModel):
    id: int
    usuario_id: UUID
    horario_id: int
    fecha_creacion: datetime
    cupos: int
    estado_pago: str
    transaction_id: Optional[str] = None

    class Config:
        orm_mode = True