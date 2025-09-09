from fastapi import APIRouter, Request, Depends, Query, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_
from typing import Optional
import math
import mercadopago
import os
from pydantic import BaseModel

from app.db import get_db
from app.models.ebooks import Ebook
from app.models.categorias_ebooks import CategoriaEbook
from app.models.compra_ebooks import CompraEbook
from app.models.user import Usuario
from app.routers.auth import current_active_user

router = APIRouter()
templates = Jinja2Templates(directory="frontend/templates")

@router.get("/ebooks")
def listar_ebooks(
    request: Request,
    categoria: Optional[int] = Query(None),
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db)
):
    """Página principal de ebooks con filtros y paginación"""
    
    # Configuración de paginación
    items_per_page = 12
    offset = (page - 1) * items_per_page
    
    # Query base para ebooks activos
    query = db.query(Ebook).options(
        joinedload(Ebook.categoria)
    ).filter(Ebook.activo == True)
    
    # Filtro por categoría
    categoria_actual = None
    if categoria:
        categoria_actual = db.query(CategoriaEbook).get(categoria)
        if categoria_actual:
            query = query.filter(Ebook.id_categoria == categoria)
    
    # Filtro por búsqueda de texto
    if q:
        search_filter = or_(
            Ebook.titulo.ilike(f"%{q}%"),
            Ebook.descripcion.ilike(f"%{q}%")
        )
        query = query.filter(search_filter)
    
    # Contar total de resultados para paginación
    total_ebooks = query.count()
    total_pages = math.ceil(total_ebooks / items_per_page)
    
    # Obtener ebooks de la página actual
    ebooks = query.order_by(Ebook.fecha_publicacion.desc()).offset(offset).limit(items_per_page).all()
    
    # Obtener categorías principales para el sidebar
    categorias_principales = db.query(CategoriaEbook).options(
        joinedload(CategoriaEbook.subcategorias)
    ).filter(CategoriaEbook.id_categoria_padre == None).all()
    
    return templates.TemplateResponse("ebooks.html", {
        "request": request,
        "ebooks": ebooks,
        "categorias_principales": categorias_principales,
        "categoria_actual": categoria_actual,
        "q": q or "",
        "page": page,
        "total_pages": total_pages,
        "total_ebooks": total_ebooks
    })

@router.get("/ebooks/pago-exitoso")
def pago_exitoso_ebook(
    request: Request,
    payment_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    external_reference: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Página de confirmación de pago exitoso para ebooks"""
    
    compra = None
    if external_reference:
        try:
            # Extraer ID de compra del external_reference
            compra_id = int(external_reference.replace("EBOOK", ""))
            compra = db.query(CompraEbook).options(
                joinedload(CompraEbook.ebook)
            ).filter(CompraEbook.id == compra_id).first()
        except ValueError:
            pass
    
    return templates.TemplateResponse("pago_exitoso_ebook.html", {
        "request": request,
        "compra": compra
    })

@router.get("/ebooks/{ebook_id}")
def detalle_ebook(
    ebook_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Página de detalle de un ebook específico"""
    
    ebook = db.query(Ebook).options(
        joinedload(Ebook.categoria)
    ).filter(
        and_(Ebook.id == ebook_id, Ebook.activo == True)
    ).first()
    
    if not ebook:
        # Redirigir a la página de ebooks si no se encuentra
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/ebooks", status_code=404)
    
    # Obtener ebooks relacionados de la misma categoría
    ebooks_relacionados = []
    if ebook.categoria:
        ebooks_relacionados = db.query(Ebook).filter(
            and_(
                Ebook.id_categoria == ebook.id_categoria,
                Ebook.id != ebook.id,
                Ebook.activo == True
            )
        ).limit(4).all()
    
    return templates.TemplateResponse("ebook_detalle.html", {
        "request": request,
        "ebook": ebook,
        "ebooks_relacionados": ebooks_relacionados
    })

class CompraEbookRequest(BaseModel):
    ebook_id: int

@router.post("/ebooks/comprar")
def comprar_ebook(
    request: CompraEbookRequest,
    usuario: Usuario = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """Endpoint para comprar un ebook usando MercadoPago"""
    
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
        metodo_pago="mercadopago"
    )
    
    db.add(nueva_compra)
    db.commit()
    db.refresh(nueva_compra)
    
    # Configurar MercadoPago
    sdk = mercadopago.SDK(os.getenv("MERCADO_PAGO_ACCESS_TOKEN"))
    
    # Crear item para MercadoPago
    items = [{
        "title": ebook.titulo,
        "quantity": 1,
        "unit_price": float(ebook.precio),
        "currency_id": "USD"
    }]
    
    # Crear preferencia de pago
    base_url = os.getenv("BASE_URL", "http://localhost:8000")
    preference_data = {
        "items": items,
        "payer": {
            "name": usuario.nombre,
            "email": usuario.email
        },
        "back_urls": {
            "success": f"{base_url}/ebooks/pago-exitoso",
            "failure": f"{base_url}/ebooks/{ebook.id}?compra=fallida",
            "pending": f"{base_url}/ebooks/{ebook.id}?compra=pendiente"
        },
        "auto_return": "approved",
        "external_reference": f"EBOOK{nueva_compra.id}",
        "notification_url": f"{base_url}/webhooks/mercadopago"
    }
    
    try:
        preference_response = sdk.preference().create(preference_data)
        preference = preference_response["response"]
        
        if preference_response["status"] == 201:
            return {
                "init_point": preference["init_point"],
                "compra_id": nueva_compra.id
            }
        else:
            raise HTTPException(status_code=500, detail="Error al crear preferencia de pago")
            
    except Exception as e:
        # Eliminar la compra si falla la creación de la preferencia
        db.delete(nueva_compra)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Error al procesar el pago: {str(e)}")

@router.get("/ebooks/{ebook_id}/descargar")
def descargar_ebook(
    ebook_id: int,
    usuario: Usuario = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """Endpoint para descargar un ebook comprado"""
    
    # Verificar que el ebook existe
    ebook = db.query(Ebook).filter(Ebook.id == ebook_id).first()
    if not ebook:
        raise HTTPException(status_code=404, detail="Ebook no encontrado")
    
    # Verificar que el usuario compró este ebook
    compra = db.query(CompraEbook).filter(
        and_(
            CompraEbook.usuario_id == usuario.id,
            CompraEbook.ebook_id == ebook_id,
            CompraEbook.estado_pago == "pagado"
        )
    ).first()
    
    if not compra:
        raise HTTPException(status_code=403, detail="No tienes acceso a este ebook")
    
    # Verificar que hay URL del archivo
    if not ebook.url_archivo:
        raise HTTPException(status_code=404, detail="No hay archivo asociado a este ebook")
    
    # Si es una URL de Cloudinary, redirigir directamente con extensión .pdf
    if ebook.url_archivo.startswith("https://res.cloudinary.com/"):
        # Agregar extensión .pdf si no la tiene
        download_url = ebook.url_archivo
        if not download_url.endswith('.pdf'):
            download_url += '.pdf'
        
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=download_url, status_code=302)
    
    # Para archivos locales, usar FileResponse
    if not os.path.exists(ebook.url_archivo):
        raise HTTPException(status_code=404, detail=f"Archivo no encontrado en la ruta: {ebook.url_archivo}")
    
    filename = f"{ebook.titulo}.pdf"
    return FileResponse(
        path=ebook.url_archivo,
        filename=filename,
        media_type='application/pdf'
    )
