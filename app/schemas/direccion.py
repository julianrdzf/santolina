from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class DireccionCreate(BaseModel):
    usuario_id: UUID
    direccion: str            # calle, número, apto
    detalle: Optional[str] = None
    ciudad: str
    codigo_postal: Optional[str] = None
    pais: str
    tipo: Optional[str] = None

class DireccionOut(BaseModel):
    id: int
    usuario_id: UUID
    direccion: str
    detalle: Optional[str] = None
    ciudad: str
    codigo_postal: Optional[str] = None
    pais: str
    tipo: Optional[str] = None

    class Config:
        orm_mode = True