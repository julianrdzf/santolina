import os
import base64
import pickle
import json
import logging
from typing import Optional
from fastapi_mail import MessageSchema  # solo para mantener la compatibilidad con tu código
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from email.mime.text import MIMEText

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GmailService:
    def __init__(self):
        self.service = None
        self.creds = None
        self._initialize_credentials()
    
    def _initialize_credentials(self):
        """Inicializa las credenciales desde variables de entorno"""
        try:
            # Obtener credenciales desde variables de entorno
            client_id = os.getenv("GMAIL_CLIENT_ID")
            client_secret = os.getenv("GMAIL_CLIENT_SECRET")
            refresh_token = os.getenv("GMAIL_REFRESH_TOKEN")
            
            if not all([client_id, client_secret, refresh_token]):
                # Fallback al método anterior si las nuevas variables no están disponibles
                token_b64 = os.getenv("GMAIL_TOKEN")
                if token_b64:
                    logger.info("Usando método de token legacy")
                    token_bytes = base64.b64decode(token_b64)
                    self.creds = pickle.loads(token_bytes)
                else:
                    raise RuntimeError("No se encontraron credenciales de Gmail válidas")
            else:
                # Crear credenciales con los nuevos parámetros
                logger.info("Usando credenciales OAuth2 modernas")
                self.creds = Credentials(
                    token=None,  # Se obtendrá al refrescar
                    refresh_token=refresh_token,
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=client_id,
                    client_secret=client_secret,
                    scopes=["https://www.googleapis.com/auth/gmail.send"]
                )
                
                # Forzar refresh inmediato para obtener access token
                logger.info("Obteniendo access token inicial...")
                self.creds.refresh(Request())
                logger.info("Access token obtenido exitosamente")
            
            # Crear servicio de Gmail
            self.service = build('gmail', 'v1', credentials=self.creds)
            logger.info("Servicio de Gmail inicializado correctamente")
            
        except Exception as e:
            logger.error(f"Error inicializando credenciales de Gmail: {e}")
            raise
    
    def _refresh_token_if_needed(self):
        """Refresca el token si es necesario"""
        try:
            if not self.creds.valid:
                if self.creds.expired and self.creds.refresh_token:
                    logger.info("Token expirado, refrescando...")
                    self.creds.refresh(Request())
                    logger.info("Token refrescado exitosamente")
                    
                    # Guardar el nuevo token si es posible
                    self._save_refreshed_token()
                else:
                    raise RuntimeError("No se puede refrescar el token: no hay refresh_token disponible")
        except Exception as e:
            logger.error(f"Error refrescando token: {e}")
            raise
    
    def _save_refreshed_token(self):
        """Guarda el token refrescado (para futuras mejoras)"""
        try:
            # Por ahora solo loggeamos el nuevo token
            # En el futuro se podría guardar en base de datos o actualizar variables de entorno
            logger.info("Token refrescado - considerar persistir para evitar futuras renovaciones")
            
            # Si quieres ver el nuevo token para actualizarlo manualmente:
            if hasattr(self.creds, 'token') and self.creds.token:
                logger.info(f"Nuevo access_token disponible (válido por ~1 hora)")
                
        except Exception as e:
            logger.warning(f"No se pudo guardar el token refrescado: {e}")
    
    def send_email(self, to_email: str, subject: str, body_html: str, from_email: Optional[str] = None):
        """Envía un email usando Gmail API con manejo automático de tokens"""
        try:
            # Verificar y refrescar token si es necesario
            self._refresh_token_if_needed()
            
            # Email por defecto
            if not from_email:
                from_email = os.getenv("GMAIL_FROM_EMAIL", "notificaciones.santolina@gmail.com")
            
            # Crear mensaje
            message = MIMEText(body_html, "html")
            message['to'] = to_email
            message['from'] = from_email
            message['subject'] = subject
            
            # Codificar y enviar
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            result = self.service.users().messages().send(
                userId="me", 
                body={'raw': raw}
            ).execute()
            
            logger.info(f"Email enviado exitosamente a {to_email} - ID: {result.get('id')}")
            return result
            
        except Exception as e:
            logger.error(f"Error enviando email a {to_email}: {e}")
            raise

# Crear instancia global del servicio
gmail_service = GmailService()

# Función de compatibilidad con el código existente
def send_email(to_email: str, subject: str, body_html: str):
    """Función de compatibilidad - envía un email usando Gmail API"""
    return gmail_service.send_email(to_email, subject, body_html)

# ------------------ Funciones adaptadas ------------------

async def enviar_mail_prueba(destinatario: str):
    content = """
    <h3>Hola, esto es una prueba de envío automático desde FastAPI.</h3>
    <p>¡Felicitaciones, tu configuración está funcionando!</p>
    """
    send_email(destinatario, "¡Correo de prueba desde Santolina!", content)

async def enviar_confirmacion_reserva(reserva, usuario):
    # Obtener información del horario y evento
    horario = reserva.horario
    fecha_evento = horario.fecha_evento
    evento = fecha_evento.evento
    
    # Formatear hora de fin
    hora_fin_str = ""
    if horario.hora_fin:
        hora_fin_str = f" - {horario.hora_fin.strftime('%H:%M')}"
    
    content = f"""
    <h3>Hola {usuario.nombre},</h3>
    <p>Gracias por reservar tu lugar en <strong>{evento.titulo}</strong>.</p>
    <p><strong>Fecha:</strong> {fecha_evento.fecha.strftime('%d/%m/%Y')}<br>
    <strong>Hora:</strong> {horario.hora_inicio.strftime('%H:%M')}{hora_fin_str}<br>
    <strong>Ubicación:</strong> {evento.ubicacion or 'A confirmar'}<br>
    <strong>Dirección:</strong> {evento.direccion or 'A confirmar'}<br>
    <strong>Cupos reservados:</strong> {reserva.cupos}</p>
    <p>Nos pondremos en contacto si hay cambios. ¡Gracias!</p>
    """
    send_email(usuario.email, f"Confirmación de tu reserva en '{evento.titulo}'", content)

async def notificar_admin_reserva(reserva, usuario):
    admin_email = os.getenv("ADMIN_EMAIL")
    if not admin_email:
        return

    # Obtener información del horario y evento
    horario = reserva.horario
    fecha_evento = horario.fecha_evento
    evento = fecha_evento.evento
    
    # Formatear hora de fin
    hora_fin_str = ""
    if horario.hora_fin:
        hora_fin_str = f" - {horario.hora_fin.strftime('%H:%M')}"

    content = f"""
    <h3>Se ha registrado una nueva reserva.</h3>
    <p><strong>Evento:</strong> {evento.titulo}<br>
    <strong>Fecha:</strong> {fecha_evento.fecha.strftime('%d/%m/%Y')}<br>
    <strong>Hora:</strong> {horario.hora_inicio.strftime('%H:%M')}{hora_fin_str}<br>
    <strong>Ubicación:</strong> {evento.ubicacion or 'A confirmar'}<br>
    <strong>Dirección:</strong> {evento.direccion or 'A confirmar'}<br>
    <strong>Nombre:</strong> {usuario.nombre}<br>
    <strong>Email:</strong> {usuario.email}<br>
    <strong>Celular:</strong> {usuario.celular or 'No proporcionado'}<br>
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

def enviar_confirmacion_orden(orden_id: int):
    """Envía email de confirmación al cliente cuando se confirma una orden"""
    from app.db import get_db
    from app.models.ordenes import Orden
    from app.models.orden_detalle import OrdenDetalle
    from app.models.user import Usuario
    from app.models.direcciones import Direccion
    from app.models.costos_envio import CostoEnvio
    from sqlalchemy.orm import joinedload
    
    try:
        # Crear nueva sesión de base de datos
        db = next(get_db())
        
        # Cargar orden con todas las relaciones necesarias
        orden = db.query(Orden).options(
            joinedload(Orden.detalle).joinedload(OrdenDetalle.producto),
            joinedload(Orden.usuario),
            joinedload(Orden.direccion_envio),
            joinedload(Orden.metodo_envio)
        ).get(orden_id)
        
        if not orden:
            print(f"❌ Orden #{orden_id} no encontrada")
            return
            
        usuario = orden.usuario
        print(f"🔄 Enviando email de confirmación de orden #{orden.id} a {usuario.email}")
        
        content = f"""
        <h2>¡Tu pedido ha sido confirmado!</h2>
        <p>Hola {usuario.nombre},</p>
        <p>Te confirmamos que hemos recibido tu pedido correctamente.</p>
        
        <h3>Detalles del pedido:</h3>
        <p><strong>Número de orden:</strong> #{orden.id}<br>
        <strong>Fecha:</strong> {orden.fecha.strftime('%d/%m/%Y %H:%M')}<br>
        <strong>Estado:</strong> {orden.estado.title()}</p>
        
        <h3>Productos:</h3>
        <ul>
        """
        
        for detalle in orden.detalle:
            content += f"<li>{detalle.producto.nombre} - Cantidad: {detalle.cantidad} - Precio: $ {detalle.precio_unitario:.2f}</li>"
        
        content += f"""
        </ul>
        
        <h3>Método de entrega:</h3>
        """
        
        # Mostrar información del método de envío
        content += f"""
        <p>{orden.metodo_envio.nombre}<br>
        {orden.metodo_envio.descripcion or ''}</p>
        """
        
        # Mostrar dirección solo si es necesaria
        if orden.direccion_envio:
            content += f"""
        <p><strong>Dirección de envío:</strong><br>
        {orden.direccion_envio.direccion}<br>
        {orden.direccion_envio.ciudad}, {orden.direccion_envio.departamento}</p>
        """
        
        content += f"""
        
        <p><strong>Total del pedido:</strong> $ {orden.total_final:.2f}</p>
        
        <p>Te contactaremos pronto para coordinar la entrega.</p>
        <p>¡Gracias por tu compra!</p>
        
        <p>Saludos,<br>
        Equipo de Santolina</p>
        """
        
        send_email(usuario.email, f"Confirmación de pedido #{orden.id} - Santolina", content)
        print(f"✅ Email de confirmación de orden enviado exitosamente a {usuario.email}")
        
    except Exception as e:
        print(f"❌ Error enviando email de confirmación de orden: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def notificar_admin_orden(orden_id: int):
    """Notifica al administrador sobre una nueva orden confirmada"""
    from app.db import get_db
    from app.models.ordenes import Orden
    from app.models.orden_detalle import OrdenDetalle
    from app.models.user import Usuario
    from app.models.direcciones import Direccion
    from app.models.costos_envio import CostoEnvio
    from sqlalchemy.orm import joinedload
    
    try:
        admin_email = os.getenv("ADMIN_EMAIL")
        if not admin_email:
            print("⚠️ ADMIN_EMAIL no configurado, no se puede enviar notificación")
            return

        # Crear nueva sesión de base de datos
        db = next(get_db())
        
        # Cargar orden con todas las relaciones necesarias
        orden = db.query(Orden).options(
            joinedload(Orden.detalle).joinedload(OrdenDetalle.producto),
            joinedload(Orden.usuario),
            joinedload(Orden.direccion_envio),
            joinedload(Orden.metodo_envio)
        ).get(orden_id)
        
        if not orden:
            print(f"❌ Orden #{orden_id} no encontrada")
            return
            
        usuario = orden.usuario
        print(f"🔄 Enviando notificación de orden #{orden.id} al admin {admin_email}")

        content = f"""
        <h2>Nueva orden confirmada</h2>
        <p>Se ha confirmado una nueva orden en la tienda.</p>
        
        <h3>Detalles del pedido:</h3>
        <p><strong>Número de orden:</strong> #{orden.id}<br>
        <strong>Fecha:</strong> {orden.fecha.strftime('%d/%m/%Y %H:%M')}<br>
        <strong>Estado:</strong> {orden.estado.title()}</p>
        
        <h3>Cliente:</h3>
        <p><strong>Nombre:</strong> {usuario.nombre}<br>
        <strong>Email:</strong> {usuario.email}<br>
        <strong>Celular:</strong> {usuario.celular or 'No proporcionado'}</p>
        
        <h3>Productos:</h3>
        <ul>
        """
        
        for detalle in orden.detalle:
            content += f"<li>{detalle.producto.nombre} - Cantidad: {detalle.cantidad} - Precio unitario: $ {detalle.precio_unitario:.2f} - Subtotal: $ {detalle.precio_unitario * detalle.cantidad:.2f}</li>"
        
        content += f"""
        </ul>
        
        <h3>Método de entrega:</h3>
        """
        
        # Mostrar información del método de envío
        content += f"""
        <p>{orden.metodo_envio.nombre}<br>
        {orden.metodo_envio.descripcion or ''}</p>
        """
        
        # Mostrar dirección solo si es necesaria
        if orden.direccion_envio:
            content += f"""
        <p><strong>Dirección de envío:</strong><br>
        {orden.direccion_envio.direccion}<br>
        {orden.direccion_envio.ciudad}, {orden.direccion_envio.departamento}<br>
        {orden.direccion_envio.pais}</p>
        """
        
        content += f"""
        
        <p><strong>Subtotal productos:</strong> $ {orden.total:.2f}<br>
        <strong>Descuento:</strong> $ {orden.descuento_total:.2f}<br>
        <strong>Total final:</strong> $ {orden.total_final:.2f}</p>
        
        <p>Método de pago: {orden.metodo_pago.upper()}</p>
        """
        
        send_email(admin_email, f"Nueva orden #{orden.id} confirmada - Santolina", content)
        print(f"✅ Notificación de orden enviada exitosamente al admin")
        
    except Exception as e:
        print(f"❌ Error enviando notificación de orden al admin: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def enviar_confirmacion_compra_ebook(compra, usuario):
    """Envía email de confirmación al cliente cuando compra un ebook"""
    try:
        print(f"🔄 Enviando email de confirmación de compra ebook #{compra.id} a {usuario.email}")
        
        # Obtener nombre de categoría de forma segura
        categoria_nombre = 'Sin categoría'
        try:
            if hasattr(compra.ebook, 'categoria') and compra.ebook.categoria:
                categoria_nombre = compra.ebook.categoria.nombre
        except:
            categoria_nombre = 'Sin categoría'
        
        content = f"""
        <h2>¡Tu ebook ha sido adquirido exitosamente!</h2>
        <p>Hola {usuario.nombre},</p>
        <p>Te confirmamos que has adquirido el ebook <strong>"{compra.ebook.titulo}"</strong> correctamente.</p>
        
        <h3>Detalles de la compra:</h3>
        <p><strong>Ebook:</strong> {compra.ebook.titulo}<br>
        <strong>Categoría:</strong> {categoria_nombre}<br>
        <strong>Precio:</strong> {compra.moneda} {compra.precio_pagado:.2f}<br>
        <strong>Fecha de compra:</strong> {compra.fecha_compra.strftime('%d/%m/%Y %H:%M')}<br>
        <strong>Estado:</strong> {compra.estado_pago.title()}</p>
        
        <h3>📥 Descarga tu ebook</h3>
        <p>Tu ebook estará disponible para descarga en tu cuenta de usuario.</p>
        <p>Puedes acceder a él en cualquier momento desde tu perfil en la sección de Mis Ebooks.</p>
                
        <p>¡Gracias por tu compra y disfruta la lectura!</p>
        
        <p>Saludos,<br>
        Equipo de Santolina</p>
        """
        
        send_email(usuario.email, f"Tu ebook '{compra.ebook.titulo}' está listo - Santolina", content)
        print(f" Email de confirmación de ebook enviado exitosamente a {usuario.email}")
        
    except Exception as e:
        print(f" Error enviando email de confirmación de ebook: {e}")
        import traceback
        traceback.print_exc()

def notificar_admin_compra_ebook(compra, usuario):
    """Notifica al administrador sobre una nueva compra de ebook"""
    try:
        admin_email = os.getenv("ADMIN_EMAIL")
        if not admin_email:
            print(" ADMIN_EMAIL no configurado, no se puede enviar notificación")
            return

        print(f" Enviando notificación de compra ebook #{compra.id} al admin {admin_email}")

        # Obtener nombre de categoría de forma segura
        categoria_nombre = 'Sin categoría'
        try:
            if hasattr(compra.ebook, 'categoria') and compra.ebook.categoria:
                categoria_nombre = compra.ebook.categoria.nombre
        except:
            categoria_nombre = 'Sin categoría'

        content = f"""
        <h2>Nueva compra de ebook confirmada</h2>
        <p>Se ha confirmado una nueva compra de ebook en la tienda digital.</p>
        
        <h3>Detalles de la compra:</h3>
        <p><strong>ID de compra:</strong> #{compra.id}<br>
        <strong>Ebook:</strong> {compra.ebook.titulo}<br>
        <strong>Categoría:</strong> {categoria_nombre}<br>
        <strong>Precio:</strong> {compra.moneda} {compra.precio_pagado:.2f}<br>
        <strong>Fecha:</strong> {compra.fecha_compra.strftime('%d/%m/%Y %H:%M')}<br>
        <strong>Estado:</strong> {compra.estado_pago.title()}</p>
        
        <h3>Cliente:</h3>
        <p><strong>Nombre:</strong> {usuario.nombre}<br>
        <strong>Email:</strong> {usuario.email}<br>
        <strong>Celular:</strong> {usuario.celular or 'No proporcionado'}</p>
        
        <h3>Información del ebook:</h3>
        <p><strong>Descripción:</strong> {compra.ebook.descripcion[:200] if compra.ebook.descripcion else 'Sin descripción'}{'...' if compra.ebook.descripcion and len(compra.ebook.descripcion) > 200 else ''}<br>
        <strong>Fecha de publicación:</strong> {compra.ebook.fecha_publicacion.strftime('%d/%m/%Y') if compra.ebook.fecha_publicacion else 'No especificada'}</p>
        
        <p><strong>💰 Total recaudado:</strong> {compra.moneda} {compra.precio_pagado:.2f}</p>
        """
        
        send_email(admin_email, f"Nueva compra de ebook: '{compra.ebook.titulo}' - Santolina", content)
        print(f"✅ Notificación de compra ebook enviada exitosamente al admin")
        
    except Exception as e:
        print(f"❌ Error enviando notificación de compra ebook al admin: {e}")
        import traceback
        traceback.print_exc()