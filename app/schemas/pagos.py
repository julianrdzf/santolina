from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PagoCreate(BaseModel):
    orden_id: int
    monto: float
    metodo: str

class PagoOut(BaseModel):
    id: int
    orden_id: int
    monto: float
    metodo: str
    estado: str
    fecha: datetime

    class Config:
        orm_mode = True