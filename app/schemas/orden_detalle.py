from pydantic import BaseModel

class OrdenDetalleCreate(BaseModel):
    orden_id: int
    producto_id: int
    cantidad: int
    precio_unitario: float

class OrdenDetalleOut(BaseModel):
    id: int
    orden_id: int
    producto_id: int
    cantidad: int
    precio_unitario: float

    class Config:
        orm_mode = True