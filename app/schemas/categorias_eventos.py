from pydantic import BaseModel
from typing import Optional, List

class CategoriaEventoBase(BaseModel):
    nombre: str
    id_categoria_padre: Optional[int] = None

class CategoriaEventoCreate(CategoriaEventoBase):
    pass

class CategoriaEventoUpdate(BaseModel):
    nombre: Optional[str] = None
    id_categoria_padre: Optional[int] = None

class CategoriaEventoOut(CategoriaEventoBase):
    id: int

    class Config:
        orm_mode = True

class CategoriaEventoWithSubcategorias(CategoriaEventoOut):
    subcategorias: List[CategoriaEventoOut] = []

    class Config:
        orm_mode = True
