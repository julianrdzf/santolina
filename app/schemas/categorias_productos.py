from pydantic import BaseModel
from typing import Optional

class CategoriaProductoCreate(BaseModel):
    nombre: str
    id_categoria_padre: Optional[int] = None

class CategoriaProductoUpdate(BaseModel):
    nombre: Optional[str] = None
    id_categoria_padre: Optional[int] = None

class CategoriaProductoOut(BaseModel):
    id: int
    nombre: str
    id_categoria_padre: Optional[int] = None

    class Config:
        orm_mode = True