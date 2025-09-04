from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class CarritoDetalleOut(BaseModel):
    id: int
    carrito_id: int
    producto_id: int
    cantidad: int

    class Config:
        orm_mode = True

class CarritoCreate(BaseModel):
    usuario_id: str  # UUID como string
    estado: Optional[str] = "activo"

class CarritoOut(BaseModel):
    id: int
    usuario_id: str
    fecha_creacion: datetime
    estado: str
    detalle: Optional[List[CarritoDetalleOut]] = []

    class Config:
        orm_mode = True