from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from app.db import SessionLocal
from app.models.evento import Evento
from app.models.fecha_evento import FechaEvento
from app.models.horario_fecha_evento import HorarioFechaEvento
from app.models.reserva import Reserva
from app.schemas.evento import EventoCreate, EventoOut
from fastapi.templating import Jinja2Templates
from typing import List, Optional
from datetime import date
from app.models.categorias_eventos import CategoriaEvento
import math

router = APIRouter()

templates = Jinja2Templates(directory="frontend/templates")

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
def mostrar_eventos_disponibles(
    request: Request, 
    db: Session = Depends(get_db), 
    categoria: Optional[int] = Query(None),
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1)
):
    # Consulta base de eventos que tienen fechas futuras con horarios
    # Solo mostrar eventos que tienen al menos una fecha >= hoy con horarios disponibles
    query = db.query(Evento).join(FechaEvento).join(HorarioFechaEvento).filter(
        FechaEvento.fecha >= date.today()
    ).distinct()
    
    # Filtro por categoría (por ID)
    categoria_actual = None
    if categoria:
        categoria_actual = db.query(CategoriaEvento).filter(CategoriaEvento.id == categoria).first()
        if categoria_actual:
            # Obtener IDs de la categoría y todas sus subcategorías
            categoria_ids = [categoria_actual.id]
            
            def get_subcategory_ids(cat_id):
                subcats = db.query(CategoriaEvento).filter(CategoriaEvento.id_categoria_padre == cat_id).all()
                for subcat in subcats:
                    categoria_ids.append(subcat.id)
                    get_subcategory_ids(subcat.id)  # Recursivo para subcategorías anidadas
            
            get_subcategory_ids(categoria_actual.id)
            query = query.filter(Evento.categoria_id.in_(categoria_ids))
    
    # Filtro por búsqueda de texto
    if q:
        search_term = f"%{q}%"
        query = query.filter(
            (Evento.titulo.ilike(search_term)) |
            (Evento.descripcion.ilike(search_term)) |
            (Evento.ubicacion.ilike(search_term))
        )
    
    # Paginación
    items_per_page = 12
    total_eventos = query.count()
    total_pages = math.ceil(total_eventos / items_per_page)
    
    offset = (page - 1) * items_per_page
    eventos = query.options(
        joinedload(Evento.categoria),
        joinedload(Evento.fechas_evento).joinedload(FechaEvento.horarios)
    ).offset(offset).limit(items_per_page).all()
    
    # Obtener categorías principales con subcategorías para el sidebar
    categorias_principales = db.query(CategoriaEvento).filter(
        CategoriaEvento.id_categoria_padre.is_(None)
    ).options(joinedload(CategoriaEvento.subcategorias)).all()
    
    return templates.TemplateResponse("eventos_disponibles.html", {
        "request": request,
        "eventos": eventos,
        "categorias_principales": categorias_principales,
        "categoria_actual": categoria_actual,
        "q": q or "",
        "page": page,
        "total_pages": total_pages,
        "total_eventos": total_eventos
    })

@router.get("/eventos/{evento_id}", response_class=HTMLResponse)
def mostrar_evento_detalle(
    evento_id: int,
    request: Request, 
    db: Session = Depends(get_db)
):
    # Obtener el evento con su categoría
    evento = db.query(Evento).options(
        joinedload(Evento.categoria)
    ).filter(Evento.id == evento_id).first()
    
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    
    # Obtener solo las fechas futuras del evento
    fechas_futuras = db.query(FechaEvento).filter(
        FechaEvento.evento_id == evento_id,
        FechaEvento.fecha >= date.today()
    ).order_by(FechaEvento.fecha.asc()).all()
    
    # Para cada fecha, filtrar solo los horarios con cupos disponibles
    for fecha in fechas_futuras:
        horarios_disponibles = []
        horarios = db.query(HorarioFechaEvento).filter(
            HorarioFechaEvento.fecha_evento_id == fecha.id
        ).order_by(HorarioFechaEvento.hora_inicio.asc()).all()
        
        for horario in horarios:
            # Calcular cupos reservados para este horario
            cupos_reservados = db.query(func.sum(Reserva.cupos)).filter(
                Reserva.horario_id == horario.id,
                Reserva.estado_pago == "aprobado"
            ).scalar() or 0
            
            # Solo incluir horarios con cupos disponibles
            cupos_disponibles = horario.cupos - cupos_reservados
            if cupos_disponibles > 0:
                horarios_disponibles.append(horario)
        
        # Asignar solo los horarios con cupos disponibles
        fecha.horarios = horarios_disponibles
    
    # Filtrar fechas que tengan al menos un horario disponible
    fechas_con_horarios = [fecha for fecha in fechas_futuras if fecha.horarios]
    
    # Asignar las fechas con horarios disponibles al evento
    evento.fechas_evento = fechas_con_horarios
    
    # Obtener eventos relacionados (misma categoría, excluyendo el actual)
    # Solo eventos que tienen fechas futuras con horarios
    eventos_relacionados = []
    if evento.categoria:
        eventos_relacionados = db.query(Evento).join(FechaEvento).join(HorarioFechaEvento).options(
            joinedload(Evento.categoria),
            joinedload(Evento.fechas_evento).joinedload(FechaEvento.horarios)
        ).filter(
            Evento.categoria_id == evento.categoria_id,
            Evento.id != evento.id,
            FechaEvento.fecha >= date.today()
        ).distinct().limit(4).all()
    
    return templates.TemplateResponse("evento_detalle.html", {
        "request": request,
        "evento": evento,
        "eventos_relacionados": eventos_relacionados
    })