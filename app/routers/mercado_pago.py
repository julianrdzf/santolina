
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
import json
import mercadopago
from app.mail_utils import enviar_confirmacion_reserva, notificar_admin_reserva, enviar_confirmacion_orden, notificar_admin_orden, enviar_confirmacion_compra_ebook, notificar_admin_compra_ebook

from app.db import get_db
from app.models.reserva import Reserva
from app.models.horario_fecha_evento import HorarioFechaEvento
from app.models.fecha_evento import FechaEvento
from app.models.evento import Evento
from app.models.ordenes import Orden
from app.models.orden_detalle import OrdenDetalle
from app.models.productos import Producto
from app.models.direcciones import Direccion
from app.models.compra_ebooks import CompraEbook
from app.models.ebooks import Ebook
import httpx
import os


from pathlib import Path
from dotenv import load_dotenv
import os

router = APIRouter()

mercado_pago_access_token = os.getenv("MERCADO_PAGO_ACCESS_TOKEN")

@router.post("/webhooks/mercadopago")
async def webhook_mercado_pago(
    request: Request,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    body = await request.json()
    tipo_evento = request.query_params.get("type")  # 'payment'
    payment_id = request.query_params.get("data.id") or body.get("data", {}).get("id")

    print("===== Webhook Mercado Pago =====")
    print(f"Tipo de evento (type): {tipo_evento}")
    print(f"Payment ID: {payment_id}")
    print("Body recibido:", body)
    print("================================")

    if tipo_evento != "payment" or not payment_id:
        return {"status": "ignored"}

    # Obtener datos del pago
    sdk = mercadopago.SDK(os.getenv("MERCADO_PAGO_ACCESS_TOKEN"))
    try:
        result = sdk.payment().get(payment_id)
        payment = result["response"]
    except Exception as e:
        print(f"Error al obtener el pago desde MP: {e}")
        return {"status": "error", "detail": str(e)}

    print("✅ Estado del pago:", payment.get("status"))
    print("🔗 External reference:", payment.get("external_reference"))

    if payment.get("status") == "approved":
        external_reference = payment.get("external_reference")
        if external_reference:
            try:
                # Determinar tipo basado en prefijo
                if external_reference.startswith("RES"):
                    # Es una reserva
                    reserva_id = int(external_reference[3:])  # Remover "RES" prefix
                    reserva = db.query(Reserva).options(
                        joinedload(Reserva.horario).joinedload(HorarioFechaEvento.fecha_evento).joinedload(FechaEvento.evento)
                    ).get(reserva_id)
                    if reserva and reserva.estado_pago != "aprobado":
                        reserva.estado_pago = "aprobado"
                        reserva.transaction_id = str(payment_id)
                        db.commit()

                        # ✅ Enviar mails de confirmación
                        background_tasks.add_task(enviar_confirmacion_reserva, reserva, reserva.usuario)
                        background_tasks.add_task(notificar_admin_reserva, reserva, reserva.usuario)

                        print("🎉 Reserva actualizada y correos enviados")
                        return {"status": "reserva updated and emails sent"}
                
                elif external_reference.startswith("ORD"):
                    # Es una orden
                    orden_id = int(external_reference[3:])  # Remover "ORD" prefix
                    orden = db.query(Orden).options(
                        joinedload(Orden.detalle).joinedload(OrdenDetalle.producto),
                        joinedload(Orden.usuario),
                        joinedload(Orden.direccion_envio)
                    ).get(orden_id)
                    if orden and orden.estado != "pagado":
                        orden.estado = "pagado"
                        orden.transaction_id = str(payment_id)
                        db.commit()
                        
                        # ✅ Enviar mails de confirmación de orden
                        background_tasks.add_task(enviar_confirmacion_orden, orden.id)
                        background_tasks.add_task(notificar_admin_orden, orden.id)
                        
                        print("🎉 Orden actualizada a pagado y correos enviados")
                        return {"status": "orden updated to paid and emails sent"}
                
                elif external_reference.startswith("EBOOK"):
                    # Es una compra de ebook
                    compra_id = int(external_reference[5:])  # Remover "EBOOK" prefix
                    print(f"🔍 Procesando compra de ebook ID: {compra_id}")
                    
                    compra = db.query(CompraEbook).options(
                        joinedload(CompraEbook.ebook).joinedload(Ebook.categoria),
                        joinedload(CompraEbook.usuario)
                    ).get(compra_id)
                    
                    if compra:
                        print(f"📚 Ebook encontrado: {compra.ebook.titulo}, Estado actual: {compra.estado_pago}")
                        if compra.estado_pago != "pagado":
                            compra.estado_pago = "pagado"
                            compra.transaction_id = str(payment_id)
                            db.commit()
                            print(f"✅ Estado actualizado a 'pagado' para compra #{compra.id}")
                            
                            # ✅ Enviar mails de confirmación de ebook
                            print(f"📧 Programando envío de emails para {compra.usuario.email}")
                            background_tasks.add_task(enviar_confirmacion_compra_ebook, compra, compra.usuario)
                            background_tasks.add_task(notificar_admin_compra_ebook, compra, compra.usuario)
                            
                            print("🎉 Compra de ebook completada y correos programados")
                            return {"status": "ebook purchase completed and emails sent"}
                        else:
                            print(f"⚠️ La compra #{compra.id} ya estaba marcada como pagada")
                            return {"status": "ebook already paid"}
                    else:
                        print(f"❌ No se encontró compra de ebook con ID: {compra_id}")
                        return {"status": "ebook purchase not found"}
                
                else:
                    # Formato anterior sin prefijo - intentar como reserva primero por compatibilidad
                    reference_id = int(external_reference)
                    
                    reserva = db.query(Reserva).options(
                        joinedload(Reserva.horario).joinedload(HorarioFechaEvento.fecha_evento).joinedload(FechaEvento.evento)
                    ).get(reference_id)
                    if reserva and reserva.estado_pago != "aprobado":
                        reserva.estado_pago = "aprobado"
                        reserva.transaction_id = str(payment_id)
                        db.commit()
                        # Enviar emails de confirmación
                        background_tasks.add_task(enviar_confirmacion_reserva, reserva, reserva.usuario)
                        background_tasks.add_task(notificar_admin_reserva, reserva, reserva.usuario)
                        print("🎉 Reserva (formato anterior) actualizada y correos enviados")
                        return {"status": "reserva updated and emails sent"}
                    
                    # Si no es reserva, intentar como orden
                    orden = db.query(Orden).options(
                        joinedload(Orden.detalle).joinedload(OrdenDetalle.producto),
                        joinedload(Orden.usuario),
                        joinedload(Orden.direccion_envio)
                    ).get(reference_id)
                    if orden and orden.estado != "pagado":
                        orden.estado = "pagado"
                        orden.transaction_id = str(payment_id)
                        db.commit()
                        background_tasks.add_task(enviar_confirmacion_orden, orden.id)
                        background_tasks.add_task(notificar_admin_orden, orden.id)
                        print("🎉 Orden (formato anterior) actualizada a pagado y correos enviados")
                        return {"status": "orden updated to paid and emails sent"}
                    
            except Exception as e:
                print(f"Error procesando webhook: {e}")
                return {"status": "error", "detail": str(e)}

    return {"status": "no_action"}