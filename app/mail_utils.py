import os
import base64
import pickle
from fastapi_mail import MessageSchema  # solo para mantener la compatibilidad con tu código
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from email.mime.text import MIMEText

# 🔹 Cargar token de Gmail desde variable de entorno
token_b64 = os.getenv("GMAIL_TOKEN")
if not token_b64:
    raise RuntimeError("GMAIL_TOKEN no está configurada en el entorno")

token_bytes = base64.b64decode(token_b64)
creds = pickle.loads(token_bytes)

service = build('gmail', 'v1', credentials=creds)

def send_email(to_email: str, subject: str, body_html: str):

    # Renovar token si es necesario
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        
    """Envía un mail usando Gmail API"""
    message = MIMEText(body_html, "html")
    message['to'] = to_email
    message['from'] = 'notificaciones.santolina@gmail.com'
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service.users().messages().send(userId="me", body={'raw': raw}).execute()


# ------------------ Funciones adaptadas ------------------

async def enviar_mail_prueba(destinatario: str):
    content = """
    <h3>Hola, esto es una prueba de envío automático desde FastAPI.</h3>
    <p>¡Felicitaciones, tu configuración está funcionando!</p>
    """
    send_email(destinatario, "¡Correo de prueba desde Santolina!", content)

async def enviar_confirmacion_reserva(reserva, evento):
    content = f"""
    <h3>Hola {reserva.nombre},</h3>
    <p>Gracias por reservar tu lugar en <strong>{evento.titulo}</strong>.</p>
    <p><strong>Fecha:</strong> {evento.fecha.strftime('%d/%m/%Y')}<br>
    <strong>Hora:</strong> {evento.hora or 'A confirmar'}<br>
    <strong>Ubicación:</strong> {evento.ubicacion or 'A confirmar'}<br>
    <strong>Dirección:</strong> {evento.direccion or 'A confirmar'}<br>
    <strong>Cupos reservados:</strong> {reserva.cupos}</p>
    <p>Nos pondremos en contacto si hay cambios. ¡Gracias!</p>
    """
    send_email(reserva.email, f"Confirmación de tu reserva en '{evento.titulo}'", content)

async def notificar_admin_reserva(reserva, evento):
    admin_email = os.getenv("ADMIN_EMAIL")
    if not admin_email:
        return

    content = f"""
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
    """
    send_email(admin_email, f"Nueva reserva registrada en '{evento.titulo}'", content)

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
    send_email(admin_email, "Nuevo mensaje de contacto", content)

async def enviar_mail_password_reset(destinatario: str, reset_link: str):
    content = f"""
    <h3>Restablecer tu contraseña</h3>
    <p>Hacé clic en el siguiente enlace para crear una nueva contraseña:</p>
    <p><a href="{reset_link}">{reset_link}</a></p>
    <p>Si no solicitaste esto, podés ignorar este mensaje.</p>
    """
    send_email(destinatario, "Restablecer contraseña", content)