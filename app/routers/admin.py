from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models.evento import Evento
from app.models.categorias import Categoria
from app.models.reserva import Reserva

from fastapi import Form
from fastapi.responses import RedirectResponse

from app.routers.auth import current_superuser


router = APIRouter()
templates = Jinja2Templates(directory="frontend/templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/admin", dependencies=[Depends(current_superuser)])
def admin_home(request: Request):
    return templates.TemplateResponse("admin_panel.html", {"request": request})

@router.get("/admin/eventos", dependencies=[Depends(current_superuser)])
def listar_eventos_admin(request: Request, db: Session = Depends(get_db)):
    eventos = db.query(Evento).all()
    return templates.TemplateResponse("admin_eventos.html", {
        "request": request,
        "eventos": eventos
    })

@router.get("/admin/eventos/crear", dependencies=[Depends(current_superuser)])
def mostrar_formulario_crear_evento(request: Request, db: Session = Depends(get_db)):
    categorias = db.query(Categoria).all()
    return templates.TemplateResponse("admin_evento_form.html", {
        "request": request,
        "categorias": categorias,
        "modo": "crear"
    })

@router.post("/admin/eventos/crear", dependencies=[Depends(current_superuser)])
def crear_evento(
    titulo: str = Form(...),
    descripcion: str = Form(...),
    fecha: str = Form(...),
    cupos: int = Form(...),
    categoria_id: int = Form(None),
    horario: str = Form(None),
    ubicacion: str = Form(None),
    direccion: str = Form(None),
    costo: float = Form(...),
    db: Session = Depends(get_db)
):
    nuevo_evento = Evento(
        titulo=titulo,
        descripcion=descripcion,
        fecha=fecha,
        cupos_totales=cupos,
        categoria_id=categoria_id,
        hora=horario,
        ubicacion=ubicacion,
        direccion=direccion,
        costo=costo
    )
    db.add(nuevo_evento)
    db.commit()
    return RedirectResponse(url="/admin/eventos", status_code=303)

@router.get("/admin/eventos/{evento_id}/editar", dependencies=[Depends(current_superuser)])
def mostrar_formulario_editar_evento(evento_id: int, request: Request, db: Session = Depends(get_db)):
    evento = db.query(Evento).get(evento_id)
    categorias = db.query(Categoria).all()
    if not evento:
        return templates.TemplateResponse("404.html", {"request": request})
    
    return templates.TemplateResponse("admin_evento_form.html", {
        "request": request,
        "evento": evento,
        "categorias": categorias,
        "modo": "editar"
    })

@router.post("/admin/eventos/{evento_id}/editar", dependencies=[Depends(current_superuser)])
def actualizar_evento(
    evento_id: int,
    titulo: str = Form(...),
    descripcion: str = Form(...),
    fecha: str = Form(...),
    cupos: int = Form(...),
    categoria_id: int = Form(None),
    horario: str = Form(None),
    ubicacion: str = Form(None),
    costo: float = Form(...),
    db: Session = Depends(get_db)
):
    evento = db.query(Evento).get(evento_id)
    if not evento:
        return RedirectResponse(url="/admin/eventos", status_code=303)

    evento.titulo = titulo
    evento.descripcion = descripcion
    evento.fecha = fecha
    evento.cupos_totales = cupos
    evento.categoria_id = categoria_id
    evento.horario = horario
    evento.ubicacion = ubicacion
    evento.costo = costo

    db.commit()
    return RedirectResponse(url="/admin/eventos", status_code=303)

@router.post("/admin/eventos/{evento_id}/eliminar", dependencies=[Depends(current_superuser)])
def eliminar_evento(evento_id: int, db: Session = Depends(get_db)):
    evento = db.query(Evento).get(evento_id)
    if evento:
        if evento.reservas:
            return templates.TemplateResponse("error_admin.html", {
                "request": {},  # o pasá request si usás plantilla con jinja
                "mensaje": "No se puede eliminar el evento porque tiene reservas registradas."
            })
        db.delete(evento)
        db.commit()
    return RedirectResponse(url="/admin/eventos", status_code=303)

@router.get("/admin/eventos/{evento_id}/reservas", dependencies=[Depends(current_superuser)])
def ver_reservas_evento(evento_id: int, request: Request, db: Session = Depends(get_db)):
    evento = db.query(Evento).get(evento_id)
    if not evento:
        return RedirectResponse(url="/admin/eventos", status_code=303)
    
    reservas = evento.reservas  # gracias a la relación ya definida
    return templates.TemplateResponse("admin_reservas_evento.html", {
        "request": request,
        "evento": evento,
        "reservas": reservas
    })

@router.post("/admin/reservas/{reserva_id}/eliminar", dependencies=[Depends(current_superuser)])
def eliminar_reserva(reserva_id: int, db: Session = Depends(get_db)):
    reserva = db.query(Reserva).get(reserva_id)
    if reserva:
        evento_id = reserva.evento_id  # para redirigir luego
        db.delete(reserva)
        db.commit()
        return RedirectResponse(f"/admin/eventos/{evento_id}/reservas", status_code=303)
    return RedirectResponse("/admin/eventos", status_code=303)