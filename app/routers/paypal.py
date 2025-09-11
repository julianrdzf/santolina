from fastapi import APIRouter, Request, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
import os
import json
import requests
from typing import Dict, Any
from pydantic import BaseModel

from app.db import get_db
from app.models.ebooks import Ebook
from app.models.compra_ebooks import CompraEbook
from app.models.user import Usuario
from app.routers.auth import current_active_user
from app.mail_utils import enviar_confirmacion_compra_ebook, notificar_admin_compra_ebook

router = APIRouter()

class PayPalConfig:
    """Configuración de PayPal"""
    def __init__(self):
        self.client_id = os.getenv("PAYPAL_CLIENT_ID")
        self.client_secret = os.getenv("PAYPAL_CLIENT_SECRET")
        self.mode = os.getenv("PAYPAL_MODE", "sandbox")  # sandbox o live
        
        if self.mode == "sandbox":
            self.base_url = "https://api-m.sandbox.paypal.com"
        else:
            self.base_url = "https://api-m.paypal.com"
    
    def get_access_token(self) -> str:
        """Obtiene token de acceso de PayPal"""
        url = f"{self.base_url}/v1/oauth2/token"
        
        headers = {
            "Accept": "application/json",
            "Accept-Language": "en_US",
        }
        
        data = "grant_type=client_credentials"
        
        response = requests.post(
            url,
            headers=headers,
            data=data,
            auth=(self.client_id, self.client_secret)
        )
        
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            raise HTTPException(status_code=500, detail="Error obteniendo token de PayPal")

class CompraEbookPayPalRequest(BaseModel):
    ebook_id: int

@router.post("/paypal/crear-orden")
def crear_orden_paypal(
    request: CompraEbookPayPalRequest,
    usuario: Usuario = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """Crear orden de pago en PayPal para un ebook"""
    
    # Verificar que el ebook existe y está activo
    ebook = db.query(Ebook).filter(
        and_(Ebook.id == request.ebook_id, Ebook.activo == True)
    ).first()
    
    if not ebook:
        raise HTTPException(status_code=404, detail="Ebook no encontrado")
    
    # Verificar si el usuario ya compró este ebook
    compra_existente = db.query(CompraEbook).filter(
        and_(
            CompraEbook.usuario_id == usuario.id,
            CompraEbook.ebook_id == request.ebook_id,
            CompraEbook.estado_pago == "pagado"
        )
    ).first()
    
    if compra_existente:
        raise HTTPException(status_code=400, detail="Ya has comprado este ebook")
    
    # Crear registro de compra
    nueva_compra = CompraEbook(
        usuario_id=usuario.id,
        ebook_id=request.ebook_id,
        precio_pagado=ebook.precio,
        estado_pago="pendiente",
        metodo_pago="paypal"
    )
    
    db.add(nueva_compra)
    db.commit()
    db.refresh(nueva_compra)
    
    try:
        # Configurar PayPal
        paypal_config = PayPalConfig()
        access_token = paypal_config.get_access_token()
        
        # Crear orden en PayPal
        base_url = os.getenv("BASE_URL", "http://localhost:8000")
        
        order_data = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "reference_id": f"EBOOK{nueva_compra.id}",
                "amount": {
                    "currency_code": "USD",
                    "value": str(ebook.precio)
                },
                "description": f"Ebook: {ebook.titulo}"
            }],
            "application_context": {
                "return_url": f"{base_url}/paypal/pago-exitoso",
                "cancel_url": f"{base_url}/ebooks/{ebook.id}?compra=cancelada"
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }
        
        response = requests.post(
            f"{paypal_config.base_url}/v2/checkout/orders",
            headers=headers,
            json=order_data
        )
        
        if response.status_code == 201:
            order = response.json()
            
            # Guardar el ID de la orden de PayPal
            nueva_compra.transaction_id = order["id"]
            db.commit()
            
            # Buscar el enlace de aprobación
            approve_link = None
            for link in order["links"]:
                if link["rel"] == "approve":
                    approve_link = link["href"]
                    break
            
            return {
                "order_id": order["id"],
                "approve_url": approve_link,
                "compra_id": nueva_compra.id
            }
        else:
            raise HTTPException(status_code=500, detail="Error al crear orden en PayPal")
            
    except Exception as e:
        # Eliminar la compra si falla la creación de la orden
        db.delete(nueva_compra)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Error al procesar el pago: {str(e)}")

@router.get("/paypal/pago-exitoso")
def pago_exitoso_paypal(
    request: Request,
    token: str,
    PayerID: str,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Capturar pago después de la aprobación del usuario"""
    
    try:
        # Configurar PayPal
        paypal_config = PayPalConfig()
        access_token = paypal_config.get_access_token()
        
        # Capturar el pago
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }
        
        response = requests.post(
            f"{paypal_config.base_url}/v2/checkout/orders/{token}/capture",
            headers=headers
        )
        
        if response.status_code == 201:
            capture_data = response.json()
            
            # Buscar la compra por transaction_id
            compra = db.query(CompraEbook).options(
                joinedload(CompraEbook.ebook),
                joinedload(CompraEbook.usuario)
            ).filter(CompraEbook.transaction_id == token).first()
            
            if compra and compra.estado_pago != "pagado":
                # Extraer moneda del capture_data si está disponible
                moneda = "USD"  # Default
                try:
                    if "purchase_units" in capture_data and len(capture_data["purchase_units"]) > 0:
                        purchase_unit = capture_data["purchase_units"][0]
                        if "payments" in purchase_unit and "captures" in purchase_unit["payments"]:
                            captures = purchase_unit["payments"]["captures"]
                            if len(captures) > 0 and "amount" in captures[0]:
                                moneda = captures[0]["amount"].get("currency_code", "USD")
                except Exception as e:
                    print(f"⚠️ No se pudo extraer moneda del capture: {e}")
                
                # Actualizar estado de la compra
                compra.estado_pago = "pagado"
                compra.moneda = moneda
                db.commit()
                
                # Enviar emails de confirmación
                background_tasks.add_task(enviar_confirmacion_compra_ebook, compra, compra.usuario)
                background_tasks.add_task(notificar_admin_compra_ebook, compra, compra.usuario)
                
                print(f"🎉 Compra de ebook #{compra.id} confirmada via PayPal")
                
                return RedirectResponse(url=f"/ebooks/pago-exitoso?payment_id={token}&status=approved&external_reference=EBOOK{compra.id}", status_code=303)
            else:
                return RedirectResponse(url="/ebooks?error=compra_no_encontrada", status_code=303)
        else:
            return RedirectResponse(url="/ebooks?error=pago_fallido", status_code=303)
            
    except Exception as e:
        print(f"❌ Error procesando pago de PayPal: {e}")
        return RedirectResponse(url="/ebooks?error=error_procesamiento", status_code=303)

@router.post("/webhooks/paypal")
async def webhook_paypal(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Webhook para recibir notificaciones de PayPal"""
    
    try:
        # Obtener datos del webhook
        webhook_data = await request.json()
        event_type = webhook_data.get("event_type")
        
        print(f"🔔 Webhook PayPal recibido: {event_type}")
        
        # Procesar eventos de pago completado
        if event_type == "CHECKOUT.ORDER.APPROVED":
            resource = webhook_data.get("resource", {})
            order_id = resource.get("id")
            
            if order_id:
                # Buscar la compra por transaction_id
                compra = db.query(CompraEbook).options(
                    joinedload(CompraEbook.ebook),
                    joinedload(CompraEbook.usuario)
                ).filter(CompraEbook.transaction_id == order_id).first()
                
                if compra and compra.estado_pago != "pagado":
                    # Extraer moneda del webhook si está disponible
                    moneda = "USD"  # Default
                    try:
                        if "purchase_units" in resource and len(resource["purchase_units"]) > 0:
                            purchase_unit = resource["purchase_units"][0]
                            if "amount" in purchase_unit:
                                moneda = purchase_unit["amount"].get("currency_code", "USD")
                    except Exception as e:
                        print(f"⚠️ No se pudo extraer moneda del webhook: {e}")
                    
                    # Actualizar estado de la compra
                    compra.estado_pago = "pagado"
                    compra.moneda = moneda
                    db.commit()
                    
                    # Enviar emails de confirmación
                    background_tasks.add_task(enviar_confirmacion_compra_ebook, compra, compra.usuario)
                    background_tasks.add_task(notificar_admin_compra_ebook, compra, compra.usuario)
                    
                    print(f"🎉 Compra de ebook #{compra.id} confirmada via webhook PayPal")
                    return {"status": "compra confirmada"}
        
        return {"status": "evento procesado"}
        
    except Exception as e:
        print(f"❌ Error procesando webhook PayPal: {e}")
        return {"status": "error", "detail": str(e)}

@router.get("/paypal/cancelar")
def cancelar_pago_paypal(
    request: Request,
    token: str,
    db: Session = Depends(get_db)
):
    """Manejar cancelación de pago"""
    
    # Buscar la compra y marcarla como cancelada
    compra = db.query(CompraEbook).filter(CompraEbook.transaction_id == token).first()
    
    if compra:
        compra.estado_pago = "cancelado"
        db.commit()
        print(f"🚫 Compra de ebook #{compra.id} cancelada por el usuario")
    
    return RedirectResponse(url="/ebooks?mensaje=pago_cancelado", status_code=303)
