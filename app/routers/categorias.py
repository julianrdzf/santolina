from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db import SessionLocal
from app.models.categorias_eventos import CategoriaEvento
from app.schemas.categorias_eventos import CategoriaEventoOut

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/categorias_eventos", response_model=List[CategoriaEventoOut])
def listar_categorias_eventos(db: Session = Depends(get_db)):
    return db.query(CategoriaEvento).all()