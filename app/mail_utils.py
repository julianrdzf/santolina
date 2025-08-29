from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr
from dotenv import load_dotenv
import os

load_dotenv()

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT")),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_FROM_NAME=os.getenv("MAIL_FROM_NAME"),
    MAIL_STARTTLS=os.getenv("MAIL_STARTTLS") == "True",
    MAIL_SSL_TLS=os.getenv("MAIL_SSL_TLS") == "True",
    USE_CREDENTIALS=True,
)

async def enviar_mail_prueba(destinatario: EmailStr):
    message = MessageSchema(
        subject="¡Correo de prueba desde Santolina!",
        recipients=[destinatario],
        body="""
        <h3>Hola, esto es una prueba de envío automático desde FastAPI.</h3>
        <p>¡Felicitaciones, tu configuración está funcionando!</p>
        """,
        subtype="html"
    )
    fm = FastMail(conf)
    await fm.send_message(message)

async def enviar_confirmacion_reserva(reserva, evento):
    message = MessageSchema(
        subject=f"Confirmación de tu reserva en '{evento.titulo}'",
        recipients=[reserva.email],
        body=f"""
        <h3>Hola {reserva.nombre},</h3>
        <p>Gracias por reservar tu lugar en <strong>{evento.titulo}</strong>.</p>
        <p><strong>Fecha:</strong> {evento.fecha.strftime('%d/%m/%Y')}<br>
        <strong>Hora:</strong> {evento.hora or 'A confirmar'}<br>
        <strong>Ubicación:</strong> {evento.ubicacion or 'A confirmar'}<br>
        <strong>Dirección:</strong> {evento.direccion or 'A confirmar'}<br>
        <strong>Cupos reservados:</strong> {reserva.cupos}</p>
        <p>Nos pondremos en contacto si hay cambios. ¡Gracias!</p>
        """,
        subtype="html"
    )
    fm = FastMail(conf)
    await fm.send_message(message)

async def notificar_admin_reserva(reserva, evento):
    admin_email = os.getenv("ADMIN_EMAIL")  # 👈 Agregalo al .env
    if not admin_email:
        return  # evita error si no está configurado

    message = MessageSchema(
        subject=f"Nueva reserva registrada en '{evento.titulo}'",
        recipients=[admin_email],
        body=f"""
        <h3>Se ha registrado una nueva reserva.</h3>
        <p><strong>Evento:</strong> {evento.titulo}<br>
        <strong>Fecha:</strong> {evento.fecha.strftime('%d/%m/%Y')}<br>
        <strong>Hora:</strong> {evento.hora or 'A confirmar'}<br>
        <strong>Ubicación:</strong> {evento.ubicacion or 'A confirmar'}<br>
        <strong>Dirección:</strong> {evento.direccion or 'A confirmar'}<br>
        <strong>Nombre:</strong> {reserva.nombre}<br>
        <strong>Email:</strong> {reserva.email}<br>
        <strong>Celular:</strong> {reserva.celular or 'No proporcionado'}<br>
        <strong>Cupos:</strong> {reserva.cupos}</p>
        """,
        subtype="html"
    )
    fm = FastMail(conf)
    await fm.send_message(message)

async def enviar_mail_contacto(nombre, email, telefono, asunto, mensaje):
    admin_email = os.getenv("ADMIN_EMAIL")
    if not admin_email:
        return

    content = f"""
    <h3>Nuevo mensaje de contacto desde la web</h3>
    <p><strong>Nombre:</strong> {nombre}</p>
    <p><strong>Email:</strong> {email}</p>
    <p><strong>Teléfono:</strong> {telefono or 'No proporcionado'}</p>
    <p><strong>Asunto:</strong> {asunto}</p>
    <p><strong>Mensaje:</strong><br>{mensaje}</p>
    """

    message = MessageSchema(
        subject="Nuevo mensaje de contacto",
        recipients=[admin_email],
        body=content,
        subtype="html"
    )

    fm = FastMail(conf)  # conf debe ser tu configuración global (igual que para reservas)
    await fm.send_message(message)


# Enviar mail para reset de password
async def enviar_mail_password_reset(destinatario: str, reset_link: str):
    message = MessageSchema(
        subject="Restablecer contraseña",
        recipients=[destinatario],
        body=f"""
        <h3>Restablecer tu contraseña</h3>
        <p>Hacé clic en el siguiente enlace para crear una nueva contraseña:</p>
        <p><a href="{reset_link}">{reset_link}</a></p>
        <p>Si no solicitaste esto, podés ignorar este mensaje.</p>
        """,
        subtype="html",
    )
    fm = FastMail(conf)
    await fm.send_message(message)