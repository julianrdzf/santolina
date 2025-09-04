from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CuponCreate(BaseModel):
    codigo: str
    descripcion: Optional[str] = None
    tipo_descuento: str  # "porcentaje" o "fijo"
    valor: float
    fecha_inicio: datetime
    fecha_fin: datetime
    activo: Optional[bool] = True

class CuponOut(BaseModel):
    id: int
    codigo: str
    descripcion: Optional[str] = None
    tipo_descuento: str
    valor: float
    fecha_inicio: datetime
    fecha_fin: datetime
    activo: bool

    class Config:
        orm_mode = True