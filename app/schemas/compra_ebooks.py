from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class CompraEbookBase(BaseModel):
    ebook_id: int
    precio_pagado: float
    metodo_pago: Optional[str] = None
    estado_pago: str = "pendiente"
    transaction_id: Optional[str] = None

class CompraEbookCreate(CompraEbookBase):
    usuario_id: UUID

class CompraEbookUpdate(BaseModel):
    estado_pago: Optional[str] = None
    transaction_id: Optional[str] = None
    codigo_descarga: Optional[str] = None

class CompraEbook(CompraEbookBase):
    id: int
    usuario_id: UUID
    fecha_compra: datetime
    codigo_descarga: Optional[str] = None

    class Config:
        from_attributes = True

class CompraEbookWithDetails(CompraEbook):
    """Schema que incluye detalles del ebook y usuario"""
    ebook: Optional[dict] = None  # Se puede expandir con EbookBase si es necesario
    usuario: Optional[dict] = None  # Se puede expandir con UserRead si es necesario
