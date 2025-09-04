from pydantic import BaseModel

class PromocionProductoCreate(BaseModel):
    id_promocion: int
    id_producto: int

class PromocionProductoOut(BaseModel):
    id: int
    id_promocion: int
    id_producto: int

    class Config:
        orm_mode = True