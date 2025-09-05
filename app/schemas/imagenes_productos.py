from pydantic import BaseModel
from typing import Optional

class ImagenProductoCreate(BaseModel):
    id_producto: int
    url_imagen: str
    descripcion: Optional[str] = None
    public_id: str

class ImagenProductoOut(BaseModel):
    id: int
    id_producto: int
    url_imagen: str
    descripcion: Optional[str] = None
    public_id: str

    class Config:
        orm_mode = True