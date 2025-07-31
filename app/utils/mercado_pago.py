import mercadopago
import os
from dotenv import load_dotenv

load_dotenv()

mercado_pago_access_token = os.getenv("MERCADO_PAGO_ACCESS_TOKEN")

sdk = mercadopago.SDK(os.getenv("MERCADO_PAGO_ACCESS_TOKEN"))

def crear_preferencia_pago(evento, reserva_temp_id, usuario_email):
    preference_data = {
        "items": [
            {
                "title": evento.titulo,
                "quantity": 1,
                "unit_price": float(evento.costo),
                "currency_id": "UYU"
            }
        ],
        "payer": {
            "email": usuario_email
        },
        "back_urls": {
            "success": f"http://localhost:8000/reserva/confirmada?reserva_id={reserva_temp_id}",
            "failure": "http://localhost:8000/reserva/fallida",
            "pending": "http://localhost:8000/reserva/pendiente"
        },
        "auto_return": "approved"
    }

    preference_response = sdk.preference().create(preference_data)
    return preference_response["response"]["init_point"]

def consultar_pago(mp_payment_id):
    url = f"https://api.mercadopago.com/v1/payments/{mp_payment_id}"
    headers = {
        "Authorization": f"Bearer {mercado_pago_access_token}"
    }
    response = requests.get(url, headers=headers)
    return response.json()