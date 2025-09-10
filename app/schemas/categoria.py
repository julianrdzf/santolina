from pydantic import BaseModel

class CategoriaEventoCreate(BaseModel):
    nombre: str

class CategoriaEventoUpdate(BaseModel):
    nombre: str

class CategoriaEventoOut(BaseModel):
    id: int
    nombre: str

    class Config:
        orm_mode = True