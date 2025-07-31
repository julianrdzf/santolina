from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from uuid import UUID

class ReservaCreate(BaseModel):
    nombre: str
    email: EmailStr
    celular: Optional[str] = None
    cupos: int
    evento_id: int
    estado_pago: Optional[str] = "pendiente"

class ReservaOut(BaseModel):
    id: int
    nombre: str
    email: EmailStr
    celular: Optional[str] = None
    cupos: int
    evento_id: int
    fecha_creacion: datetime
    usuario_id: Optional[UUID] = None
    estado_pago: str

    class Config:
        orm_mode = True