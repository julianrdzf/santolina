from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class EbookBase(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    precio: float
    imagen_portada: Optional[str] = None
    imagen_public_id: Optional[str] = None  
    url_archivo: str
    archivo_public_id: str
    id_categoria: Optional[int] = None
    activo: bool = True

class EbookCreate(EbookBase):
    pass

class EbookUpdate(BaseModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    precio: Optional[float] = None
    imagen_portada: Optional[str] = None
    imagen_public_id: Optional[str] = None  
    url_archivo: Optional[str] = None
    archivo_public_id: Optional[str] = None
    id_categoria: Optional[int] = None
    activo: Optional[bool] = None

class Ebook(EbookBase):
    id: int
    fecha_publicacion: datetime

    class Config:
        from_attributes = True
