from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class CuponUsoCreate(BaseModel):
    cupon_id: int
    usuario_id: UUID

class CuponUsoOut(BaseModel):
    id: int
    cupon_id: int
    usuario_id: UUID
    fecha_uso: datetime

    class Config:
        orm_mode = True