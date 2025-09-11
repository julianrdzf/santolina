from pydantic import BaseModel
from typing import Optional

class CostoEnvioBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    costo: float
    url_imagen: Optional[str] = None
    activo: bool = True
    requiere_direccion: bool = True

class CostoEnvioCreate(CostoEnvioBase):
    pass

class CostoEnvioUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    costo: Optional[float] = None
    url_imagen: Optional[str] = None
    activo: Optional[bool] = None
    requiere_direccion: Optional[bool] = None

class CostoEnvio(CostoEnvioBase):
    id: int

    class Config:
        from_attributes = True
