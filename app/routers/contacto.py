from fastapi import APIRouter, Form, BackgroundTasks
from app.mail_utils import enviar_mail_contacto

router = APIRouter()

@router.post("/enviar-contacto")
async def enviar_contacto(
    background_tasks: BackgroundTasks,
    nombre: str = Form(...),
    email: str = Form(...),
    telefono: str = Form(None),
    servicio: str = Form(...),
    mensaje: str = Form(...)
):
    background_tasks.add_task(enviar_mail_contacto, nombre, email, telefono, servicio, mensaje)
    return {"success": True}