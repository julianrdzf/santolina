
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from fastapi import APIRouter, Request
import json
import mercadopago
from fastapi import BackgroundTasks
from app.mail_utils import enviar_confirmacion_reserva, notificar_admin_reserva

from app.db import get_db
from app.models.reserva import Reserva
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
                reserva_id = int(external_reference)
                reserva = db.query(Reserva).get(reserva_id)
                if reserva and reserva.estado_pago != "aprobado":
                    reserva.estado_pago = "aprobado"
                    db.commit()

                    # ✅ Enviar mails
                    background_tasks.add_task(enviar_confirmacion_reserva, reserva, reserva.evento)
                    background_tasks.add_task(notificar_admin_reserva, reserva, reserva.evento)

                    print("🎉 Reserva actualizada y correos enviados")
                    return {"status": "updated and emails sent"}
            except Exception as e:
                print(f"Error procesando webhook: {e}")
                return {"status": "error", "detail": str(e)}

    return {"status": "no_action"}