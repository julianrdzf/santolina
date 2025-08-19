from pydantic import BaseModel

class CategoriaOut(BaseModel):
    id: int
    nombre: str

    class Config:
        orm_mode = True