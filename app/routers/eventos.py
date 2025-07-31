from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models.evento import Evento
from app.schemas.evento import EventoCreate, EventoOut
from fastapi.templating import Jinja2Templates
from typing import List
from datetime import date
from app.models.categorias import Categoria


from app.db import SessionLocal
from app.models.evento import Evento

router = APIRouter()


templates = Jinja2Templates(directory="frontend/templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/eventos", response_model=EventoOut)
def crear_evento(evento: EventoCreate, db: Session = Depends(get_db)):
    nuevo_evento = Evento(**evento.dict())
    db.add(nuevo_evento)
    db.commit()
    db.refresh(nuevo_evento)
    return nuevo_evento

@router.get("/eventos", response_model=List[EventoOut])
def listar_eventos(db: Session = Depends(get_db)):
    return db.query(Evento).all()

@router.get("/eventos-disponibles", response_class=HTMLResponse)
def mostrar_eventos_disponibles(request: Request, db: Session = Depends(get_db), categoria: str = Query(None)):
    query = db.query(Evento).filter(Evento.fecha >= date.today())

    if categoria:
        query = query.join(Categoria).filter(Categoria.nombre == categoria)

    eventos = query.all()
    categorias = db.query(Categoria).all()  # Para armar el menú si querés
    return templates.TemplateResponse("eventos_disponibles.html", {
        "request": request,
        "eventos": eventos,
        "categorias": categorias,
        "categoria_seleccionada": categoria
    })