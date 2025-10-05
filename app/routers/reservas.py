from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from fastapi.templating import Jinja2Templates
from app.db import SessionLocal
from app.models.reserva import Reserva
from app.models.evento import Evento
from app.models.fecha_evento import FechaEvento
from app.models.horario_fecha_evento import HorarioFechaEvento
from app.schemas.reserva import ReservaCreate, ReservaOut
from fastapi import Form, BackgroundTasks
from fastapi.responses import RedirectResponse, HTMLResponse
from app.mail_utils import enviar_confirmacion_reserva, notificar_admin_reserva
from app.routers.auth import current_active_user, optional_current_user
from app.models.user import Usuario
from typing import Optional

import mercadopago
from pathlib import Path
from dotenv import load_dotenv
import os

env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
sdk = mercadopago.SDK(os.getenv("MERCADO_PAGO_ACCESS_TOKEN"))
base_url = os.getenv("BASE_URL")


router = APIRouter()
templates = Jinja2Templates(directory="frontend/templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/reservas/{evento_id}")
def formulario_reserva(
    evento_id: int,
    request: Request,
    fecha: Optional[int] = None,
    horario: Optional[int] = None,
    db: Session = Depends(get_db),
    usuario: Optional[Usuario] = Depends(optional_current_user)
):
    # Verificar si el usuario está logueado
    if not usuario:
        # Redirigir a la página de evento_detalle después del login
        redirect_url = f"/eventos/{evento_id}"
        return templates.TemplateResponse("reserva_login_requerido.html", {
            "request": request,
            "redirect_url": redirect_url
        })
    
    evento = db.query(Evento).get(evento_id)
    if not evento:
        return templates.TemplateResponse("404.html", {"request": request})

    # Obtener la fecha y horario seleccionados
    fecha_evento = None
    horario_evento = None
    
    if fecha:
        fecha_evento = db.query(FechaEvento).filter(
            FechaEvento.id == fecha,
            FechaEvento.evento_id == evento_id
        ).first()
    
    if horario and fecha_evento:
        horario_evento = db.query(HorarioFechaEvento).filter(
            HorarioFechaEvento.id == horario,
            HorarioFechaEvento.fecha_evento_id == fecha_evento.id
        ).first()

    return templates.TemplateResponse("reservas.html", {
        "request": request,
        "evento": evento,
        "fecha_evento": fecha_evento,
        "horario_evento": horario_evento,
        "usuario": usuario
    })

@router.post("/reservas")
def crear_reserva_con_pago(
    request: Request,
    evento_id: int = Form(...),
    fecha_evento_id: Optional[int] = Form(None),
    horario_id: Optional[int] = Form(None),
    nombre: str = Form(...),
    email: str = Form(...),
    celular: str = Form(...),
    cantidad: int = Form(...),
    db: Session = Depends(get_db),
    usuario: Optional[Usuario] = Depends(optional_current_user)
):
    evento = db.query(Evento).filter(Evento.id == evento_id).first()
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")

    # Validar que se proporcione horario_id (obligatorio en nueva estructura)
    if not horario_id:
        raise HTTPException(status_code=400, detail="Horario es requerido")
        
    # Obtener el horario seleccionado
    horario_evento = db.query(HorarioFechaEvento).filter(HorarioFechaEvento.id == horario_id).first()
    if not horario_evento:
        raise HTTPException(status_code=400, detail="Horario no encontrado")
    
    # El precio viene del evento base
    precio_unitario = evento.costo if evento.costo else 0

    # Verificar cupos disponibles para este horario específico
    cupos_reservados = db.query(func.sum(Reserva.cupos)).filter(
        Reserva.horario_id == horario_id, 
        Reserva.estado_pago == "aprobado"
    ).scalar() or 0
    cupos_disponibles = horario_evento.cupos - cupos_reservados

    if cantidad > cupos_disponibles:
        return templates.TemplateResponse("reserva_error.html", {
            "request": request,
            "mensaje": f"Cupos disponibles para este horario: {cupos_disponibles}",
            "evento": evento
        })
    
    # Actualizar celular del usuario si no lo tenía y se proporcionó
    if usuario and celular and not usuario.celular:
        usuario_db = db.query(Usuario).filter(Usuario.id == usuario.id).first()
        if usuario_db:
            usuario_db.celular = celular
            db.commit()
            db.refresh(usuario_db)

    # ✅ Crear reserva con nueva estructura (horario_id es obligatorio)
    nueva_reserva = Reserva(
        horario_id=horario_id,
        usuario_id=usuario.id if usuario else None,
        cupos=cantidad,
        estado_pago="pendiente"
    )
    db.add(nueva_reserva)
    db.commit()
    db.refresh(nueva_reserva)

    # Crear preferencia de pago
    sdk = mercadopago.SDK(os.getenv("MERCADO_PAGO_ACCESS_TOKEN"))
    preference_data = {
        "items": [{
            "title": f"{evento.titulo}",
            "quantity": cantidad,
            "unit_price": float(precio_unitario),
            "currency_id": "UYU"
        }],
        "payer": {
            "name": nombre,
            "email": email,
        },
        "back_urls": {
            "success": f"{base_url}/pago-exitoso?reserva_id={nueva_reserva.id}",
            "failure": f"{base_url}/pago-error",
            "pending": f"{base_url}/pago-pendiente"
        },
        "auto_return": "approved",
        "external_reference": f"RES{nueva_reserva.id}",
        "notification_url": f"{base_url}/webhooks/mercadopago"
    }

    preference_response = sdk.preference().create(preference_data)
    preference = preference_response["response"]

    return RedirectResponse(url=preference["init_point"], status_code=303)

@router.get("/pago-exitoso")
def pago_exitoso(
    request: Request,
    reserva_id: int,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    reserva = db.query(Reserva).options(
        joinedload(Reserva.horario).joinedload(HorarioFechaEvento.fecha_evento).joinedload(FechaEvento.evento)
    ).get(reserva_id)
    if not reserva:
        return templates.TemplateResponse("404.html", {"request": request})

    if reserva.estado_pago != "aprobado":
        reserva.estado_pago = "aprobado"
        db.commit()
        db.refresh(reserva)

        # Enviar emails de confirmación
        background_tasks.add_task(enviar_confirmacion_reserva, reserva, reserva.usuario)
        background_tasks.add_task(notificar_admin_reserva, reserva, reserva.usuario)

    return RedirectResponse(url=f"/reserva-confirmada/{reserva.id}", status_code=303)

@router.get("/reserva-confirmada/{reserva_id}")
def reserva_confirmada(reserva_id: int, request: Request, db: Session = Depends(get_db)):
    reserva = db.query(Reserva).options(
        joinedload(Reserva.horario).joinedload(HorarioFechaEvento.fecha_evento).joinedload(FechaEvento.evento)
    ).get(reserva_id)
    if not reserva:
        return templates.TemplateResponse("404.html", {"request": request})
    
    # Acceder al evento a través de la nueva estructura
    evento = reserva.horario.fecha_evento.evento

    return templates.TemplateResponse("reserva_confirmada.html", {
        "request": request,
        "reserva": reserva,
        "evento": evento
    })

@router.get("/reserva-error", response_class=HTMLResponse)
def reserva_error(request: Request, mensaje: str):
    return templates.TemplateResponse("reserva_error.html", {
        "request": request,
        "mensaje": mensaje
    })

@router.get("/pago-error", response_class=HTMLResponse)
async def pago_error(request: Request):
    return templates.TemplateResponse("pago_error.html", {
        "request": request,
        "mensaje": "Hubo un problema con el pago. Por favor, intenta nuevamente."
    })


@router.get("/pago-pendiente")
def pago_pendiente(
    request: Request, 
    external_reference: str,
    db: Session = Depends(get_db)    
):
    # Extraer ID de reserva del external_reference con prefijo
    if external_reference.startswith("RES"):
        reserva_id = int(external_reference[3:])  # Remover "RES" prefix
    else:
        reserva_id = int(external_reference)  # Compatibilidad con formato anterior
    
    reserva = db.query(Reserva).get(reserva_id)
    evento = reserva.evento

    if reserva.estado_pago == "pendiente":
        reserva.estado_pago = "en_proceso"
        db.commit()
        db.refresh(reserva)
    
    return templates.TemplateResponse("pago_pendiente.html", {
        "request": request,
        "evento": evento,
        "referencia": external_reference
    })