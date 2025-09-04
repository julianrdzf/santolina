from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class PromocionCreate(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    tipo_descuento: str  # "porcentaje" o "fijo"
    valor: float
    fecha_inicio: datetime
    fecha_fin: datetime
    activo: Optional[bool] = True

class PromocionOut(BaseModel):
    id: int
    titulo: str
    descripcion: Optional[str] = None
    tipo_descuento: str
    valor: float
    fecha_inicio: datetime
    fecha_fin: datetime
    activo: bool

    class Config:
        orm_mode = True