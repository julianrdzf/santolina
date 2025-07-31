from pydantic import BaseModel
from datetime import date
from typing import Optional
from app.schemas.categoria import CategoriaOut
from decimal import Decimal

class EventoCreate(BaseModel):
    titulo: str
    descripcion: str = ""
    fecha: date
    cupos_totales: int
    categoria_id: Optional[int]
    hora: Optional[str] = None         
    ubicacion: Optional[str] = None
    direccion: Optional[str] = None
    costo: Optional[Decimal]

class EventoOut(BaseModel):
    id: int
    titulo: str
    descripcion: Optional[str]
    fecha: date
    cupos_totales: int
    categoria: Optional[CategoriaOut]

    class Config:
        orm_mode = True