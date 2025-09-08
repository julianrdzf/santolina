from pydantic import BaseModel
from typing import Optional

class CostoEnvioBase(BaseModel):
    departamento: str
    costo: float
    activo: bool = True

class CostoEnvioCreate(CostoEnvioBase):
    pass

class CostoEnvioUpdate(BaseModel):
    departamento: Optional[str] = None
    costo: Optional[float] = None
    activo: Optional[bool] = None

class CostoEnvio(CostoEnvioBase):
    id: int

    class Config:
        from_attributes = True
