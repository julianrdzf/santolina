from pydantic import BaseModel
from typing import Optional
from app.schemas.categorias_eventos import CategoriaEventoOut
from decimal import Decimal

class EventoCreate(BaseModel):
    titulo: str
    descripcion: str = ""
    categoria_id: Optional[int]
    ubicacion: Optional[str] = None
    direccion: Optional[str] = None
    costo: Optional[Decimal]
    costo_dolares: Optional[Decimal] = None
    imagen: Optional[str] = None
    imagen_public_id: Optional[str] = None
    prioridad: Optional[int] = None

class EventoOut(BaseModel):
    id: int
    titulo: str
    descripcion: Optional[str]
    categoria: Optional[CategoriaEventoOut]
    ubicacion: Optional[str]
    direccion: Optional[str]
    costo: Optional[Decimal]
    costo_dolares: Optional[Decimal]
    imagen: Optional[str]
    imagen_public_id: Optional[str]
    prioridad: Optional[int] = None

    class Config:
        orm_mode = True