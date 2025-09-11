from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class OrdenDetalleOut(BaseModel):
    id: int
    orden_id: int
    producto_id: int
    cantidad: int
    precio_unitario: float

    class Config:
        orm_mode = True

class OrdenCreate(BaseModel):
    usuario_id: str  # UUID como string
    direccion_envio_id: Optional[int] = None
    metodo_envio_id: int
    metodo_pago: Optional[str] = None
    total: float
    descuento_total: Optional[float] = 0
    total_final: float

class OrdenOut(BaseModel):
    id: int
    usuario_id: str
    fecha: datetime
    total: float
    estado: str
    direccion_envio_id: Optional[int] = None
    metodo_envio_id: int
    metodo_pago: Optional[str] = None
    descuento_total: float
    total_final: float
    detalle: Optional[List[OrdenDetalleOut]] = []

    class Config:
        orm_mode = True