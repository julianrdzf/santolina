from pydantic import BaseModel
from typing import Optional, List

class CategoriaEbookBase(BaseModel):
    nombre: str
    id_categoria_padre: Optional[int] = None

class CategoriaEbookCreate(CategoriaEbookBase):
    pass

class CategoriaEbookUpdate(BaseModel):
    nombre: Optional[str] = None
    id_categoria_padre: Optional[int] = None

class CategoriaEbook(CategoriaEbookBase):
    id: int

    class Config:
        from_attributes = True

class CategoriaEbookWithSubcategorias(CategoriaEbook):
    subcategorias: List[CategoriaEbook] = []

    class Config:
        from_attributes = True
