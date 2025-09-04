from pydantic import BaseModel

class CarritoDetalleCreate(BaseModel):
    carrito_id: int
    producto_id: int
    cantidad: int

class CarritoDetalleOut(BaseModel):
    id: int
    carrito_id: int
    producto_id: int
    cantidad: int

    class Config:
        orm_mode = True