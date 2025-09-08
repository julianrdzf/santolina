from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi.templating import Jinja2Templates
from app.db import SessionLocal
from app.models.reserva import Reserva
from app.models.evento import Evento
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
    db: Session = Depends(get_db),
    usuario: Optional[Usuario] = Depends(optional_current_user)  # 👈 opcional
):
    evento = db.query(Evento).get(evento_id)
    if not evento:
        return templates.TemplateResponse("404.html", {"request": request})

    return templates.TemplateResponse("reservas.html", {
        "request": request,
        "evento": evento,
        "usuario": usuario  # 👈 lo pasás al template
    })

@router.post("/reservas")
def crear_reserva_con_pago(
    request: Request,
    evento_id: int = Form(...),
    nombre: str = Form(...),
    email: str = Form(...),
    celular: str = Form(None),
    cantidad: int = Form(...),
    db: Session = Depends(get_db),
    usuario: Optional[Usuario] = Depends(optional_current_user)
):
    evento = db.query(Evento).filter(Evento.id == evento_id).first()
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")

    # Verificar cupos disponibles
    cupos_reservados = db.query(func.sum(Reserva.cupos)).filter(Reserva.evento_id == evento_id, Reserva.estado_pago == "aprobado").scalar() or 0
    cupos_disponibles = evento.cupos_totales - cupos_reservados

    if cantidad > cupos_disponibles:
        return templates.TemplateResponse("reserva_error.html", {
            "request": request,
            "mensaje": f"Cupos disponibles: {cupos_disponibles}",
            "evento": evento
        })

    # ✅ Crear reserva con estado "pendiente"
    nueva_reserva = Reserva(
        evento_id=evento.id,
        nombre=nombre,
        email=email,
        celular=celular,
        cupos=cantidad,
        usuario_id=usuario.id if usuario else None,
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
            "unit_price": float(evento.costo),
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
    reserva = db.query(Reserva).get(reserva_id)
    if not reserva:
        return templates.TemplateResponse("404.html", {"request": request})

    if reserva.estado_pago != "aprobado":
        reserva.estado_pago = "aprobado"
        db.commit()
        db.refresh(reserva)

        background_tasks.add_task(enviar_confirmacion_reserva, reserva, reserva.evento)
        background_tasks.add_task(notificar_admin_reserva, reserva, reserva.evento)

    return RedirectResponse(url=f"/reserva-confirmada/{reserva.id}", status_code=303)

@router.get("/reserva-confirmada/{reserva_id}")
def reserva_confirmada(reserva_id: int, request: Request, db: Session = Depends(get_db)):
    reserva = db.query(Reserva).get(reserva_id)
    if not reserva:
        return templates.TemplateResponse("404.html", {"request": request})
    
    # Cargar evento explícitamente si no viene precargado
    evento = reserva.evento

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