from pydantic import BaseModel
from typing import Optional, List
from .categorias_productos import CategoriaProductoOut
from .imagenes_productos import ImagenProductoOut

class ProductoCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    precio: float
    stock: int
    id_categoria: int

class ProductoOut(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None
    precio: float
    stock: int
    id_categoria: int
    categoria: Optional[CategoriaProductoOut] = None
    imagenes: Optional[List[ImagenProductoOut]] = []

    class Config:
        orm_mode = True