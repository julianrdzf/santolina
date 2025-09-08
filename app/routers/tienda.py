from fastapi import APIRouter, Request, Depends, Query, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.db import get_db
from app.models.categorias_productos import CategoriaProducto
from app.models.productos import Producto
from app.models.user import Usuario
from app.models.promociones import Promocion
from app.models.promocion_productos import PromocionProducto
from app.models.cupones import Cupon
from app.models.cupones_uso import CuponUso

from app.models.carritos import Carrito
from app.models.carrito_detalle import CarritoDetalle
from app.models.direcciones import Direccion
from app.models.ordenes import Orden
from app.models.orden_detalle import OrdenDetalle
from app.models.costos_envio import CostoEnvio

import mercadopago
from pathlib import Path
from dotenv import load_dotenv
import os

env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
base_url = os.getenv("BASE_URL")

from app.routers.auth import current_active_user, optional_current_user
from app.mail_utils import enviar_confirmacion_orden, notificar_admin_orden
from fastapi import BackgroundTasks
from sqlalchemy.orm import joinedload
from sqlalchemy import and_
from datetime import datetime, date
from app.models.orden_detalle import OrdenDetalle
from app.models.productos import Producto
from app.models.direcciones import Direccion

router = APIRouter()
templates = Jinja2Templates(directory="frontend/templates")

@router.get("/tienda")
def tienda(
    request: Request,
    db: Session = Depends(get_db),
    page: int = 1,
    q: str = "",
    categoria: Optional[int] = Query(None)
):
    query = db.query(Producto)

    # Filtro por búsqueda de texto
    if q:
        query = query.filter(
            Producto.nombre.ilike(f"%{q}%") |
            Producto.descripcion.ilike(f"%{q}%")
        )
    
    # Filtro por categoría (incluyendo subcategorías)
    categoria_actual = None
    if categoria:
        categoria_actual = db.query(CategoriaProducto).filter(CategoriaProducto.id == categoria).first()
        if categoria_actual:
            # Obtener todas las subcategorías recursivamente
            def get_all_subcategory_ids(cat_id):
                subcats = db.query(CategoriaProducto).filter(CategoriaProducto.id_categoria_padre == cat_id).all()
                ids = [cat_id]
                for subcat in subcats:
                    ids.extend(get_all_subcategory_ids(subcat.id))
                return ids
            
            category_ids = get_all_subcategory_ids(categoria)
            query = query.filter(Producto.id_categoria.in_(category_ids))

    items_per_page = 12
    total = query.count()
    productos = query.offset((page-1)*items_per_page).limit(items_per_page).all()
    
    # Agregar información de promociones a cada producto
    for producto in productos:
        producto.promocion_activa = get_promocion_activa(db, producto.id)
        if producto.promocion_activa:
            producto.precio_con_descuento = calcular_precio_con_descuento(
                producto.precio, 
                producto.promocion_activa.tipo_descuento, 
                producto.promocion_activa.valor
            )
    total_pages = (total + items_per_page - 1) // items_per_page

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        # Devolver solo el HTML del grid (partial)
        return templates.TemplateResponse(
            "partials/productos_grid.html",
            {"request": request, "productos": productos}
        )

    # Obtener categorías principales (sin padre)
    categorias_principales = db.query(CategoriaProducto).filter(
        CategoriaProducto.id_categoria_padre.is_(None)
    ).all()

    return templates.TemplateResponse("tienda.html", {
        "request": request,
        "productos": productos,
        "categorias_principales": categorias_principales,
        "categoria_actual": categoria_actual,
        "q": q,
        "page": page,
        "total_pages": total_pages
    })


def get_promocion_activa(db: Session, producto_id: int):
    """Obtiene la promoción activa para un producto específico"""
    ahora = datetime.now()
    
    # Debug: imprimir información
    print(f"Buscando promoción para producto {producto_id} en fecha {ahora}")
    
    promocion = db.query(Promocion).join(PromocionProducto).filter(
        and_(
            PromocionProducto.id_producto == producto_id,
            Promocion.activo == True,
            Promocion.fecha_inicio <= ahora,
            Promocion.fecha_fin >= ahora
        )
    ).first()
    
    if promocion:
        print(f"Promoción encontrada: {promocion.titulo}, activa: {promocion.activo}")
    else:
        print(f"No se encontró promoción activa para producto {producto_id}")
        # Verificar si hay promociones vinculadas pero inactivas
        todas_promociones = db.query(Promocion).join(PromocionProducto).filter(
            PromocionProducto.id_producto == producto_id
        ).all()
        print(f"Total promociones vinculadas: {len(todas_promociones)}")
        for p in todas_promociones:
            print(f"  - {p.titulo}: activa={p.activo}, inicio={p.fecha_inicio}, fin={p.fecha_fin}")
    
    return promocion


def calcular_precio_con_descuento(precio_original: float, tipo_descuento: str, valor: float):
    """Calcula el precio con descuento aplicado"""
    if tipo_descuento == 'porcentaje':
        return precio_original * (1 - valor / 100)
    else:  # descuento fijo
        return max(0, precio_original - valor)


@router.get("/tienda/producto/{producto_id}")
def producto_detalle(
    request: Request,
    producto_id: int,
    db: Session = Depends(get_db)
):
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        return templates.TemplateResponse(
            "tienda.html",
            {
                "request": request,
                "productos": [],
                "categorias": db.query(CategoriaProducto).all(),
                "page": 1,
                "total_pages": 1,
                "q": "",
                "selected_cats": []
            },
            status_code=404
        )

    # Agregar información de promoción al producto
    producto.promocion_activa = get_promocion_activa(db, producto.id)
    if producto.promocion_activa:
        producto.precio_con_descuento = calcular_precio_con_descuento(
            producto.precio, 
            producto.promocion_activa.tipo_descuento, 
            producto.promocion_activa.valor
        )

    return templates.TemplateResponse(
        "producto.html",
        {
            "request": request,
            "producto": producto
        }
    )


@router.post("/tienda/carrito/agregar/{producto_id}")
def agregar_al_carrito(
    request: Request,
    producto_id: int,
    cantidad: int = Form(1),
    db: Session = Depends(get_db),
    usuario: Optional[Usuario] = Depends(optional_current_user)
):
    # 1. Usuario no logueado → mostrar página intermedia
    if not usuario:
        return templates.TemplateResponse("carrito_login_requerido.html", {
            "request": request
        })

    # 2. Verificar producto
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # 3. Buscar carrito activo del usuario
    carrito = db.query(Carrito).filter(
        Carrito.usuario_id == usuario.id,
        Carrito.estado == "activo"
    ).first()

    if not carrito:
        carrito = Carrito(usuario_id=usuario.id)
        db.add(carrito)
        db.commit()
        db.refresh(carrito)

    # 4. Buscar producto dentro del carrito
    detalle = db.query(CarritoDetalle).filter(
        CarritoDetalle.carrito_id == carrito.id,
        CarritoDetalle.producto_id == producto.id
    ).first()

    if detalle:
        detalle.cantidad += cantidad
    else:
        detalle = CarritoDetalle(
            carrito_id=carrito.id,
            producto_id=producto.id,
            cantidad=cantidad
        )
        db.add(detalle)

    db.commit()

    # 5. Redirigir al carrito
    return RedirectResponse(url="/tienda/carrito", status_code=303)


@router.get("/tienda/carrito", response_class=HTMLResponse)
def ver_carrito(request: Request, db: Session = Depends(get_db), usuario: Optional[Usuario] = Depends(optional_current_user)):
    # Si no hay usuario logueado, mostrar página de login requerido
    if not usuario:
        return templates.TemplateResponse("carrito_login_requerido.html", {"request": request})

    # Buscar el carrito activo del usuario
    carrito = db.query(Carrito).filter(Carrito.usuario_id == usuario.id, Carrito.estado == "activo").first()

    # Si no existe carrito, creamos uno vacío
    if not carrito:
        carrito = Carrito(usuario_id=usuario.id)
        db.add(carrito)
        db.commit()
        db.refresh(carrito)

    # Obtener los detalles del carrito (productos)
    detalles = db.query(CarritoDetalle).filter(CarritoDetalle.carrito_id == carrito.id).all()

    # Agregar información de promociones a cada producto del carrito
    total_carrito = 0
    total_descuentos = 0
    
    for detalle in detalles:
        # Obtener promoción activa para cada producto
        detalle.producto.promocion_activa = get_promocion_activa(db, detalle.producto.id)
        
        if detalle.producto.promocion_activa:
            # Calcular precio con descuento
            precio_con_descuento = calcular_precio_con_descuento(
                detalle.producto.precio,
                detalle.producto.promocion_activa.tipo_descuento,
                detalle.producto.promocion_activa.valor
            )
            detalle.producto.precio_con_descuento = precio_con_descuento
            
            # Calcular totales con descuento
            subtotal_original = detalle.producto.precio * detalle.cantidad
            subtotal_con_descuento = precio_con_descuento * detalle.cantidad
            descuento_item = subtotal_original - subtotal_con_descuento
            
            detalle.subtotal_original = subtotal_original
            detalle.subtotal_con_descuento = subtotal_con_descuento
            detalle.descuento_aplicado = descuento_item
            
            total_carrito += subtotal_con_descuento
            total_descuentos += descuento_item
        else:
            # Sin promoción, usar precio normal
            subtotal = detalle.producto.precio * detalle.cantidad
            detalle.subtotal_original = subtotal
            detalle.subtotal_con_descuento = subtotal
            detalle.descuento_aplicado = 0
            total_carrito += subtotal
    
    # Calcular la cantidad total de productos
    cantidad_total_productos = sum(detalle.cantidad for detalle in detalles)
    
    # Total original (sin descuentos)
    total_original = sum(detalle.subtotal_original for detalle in detalles)

    # Asignar los detalles al carrito para que el template pueda accederlos
    carrito.detalle = detalles
    
    return templates.TemplateResponse("carrito.html", {
        "request": request,
        "carrito": carrito,
        "detalles": detalles,
        "total_carrito": total_carrito,
        "total_original": total_original,
        "total_descuentos": total_descuentos,
        "cantidad_total_productos": cantidad_total_productos
    })


@router.post("/tienda/carrito/eliminar/{detalle_id}")
def eliminar_del_carrito(
    request: Request,
    detalle_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(current_active_user)
):
    # Buscar el detalle del carrito
    detalle = db.query(CarritoDetalle).filter(CarritoDetalle.id == detalle_id).first()
    
    if not detalle:
        raise HTTPException(status_code=404, detail="Producto no encontrado en el carrito")
    
    # Verificar que el carrito pertenece al usuario actual
    carrito = db.query(Carrito).filter(
        Carrito.id == detalle.carrito_id,
        Carrito.usuario_id == usuario.id
    ).first()
    
    if not carrito:
        raise HTTPException(status_code=403, detail="No tienes permisos para eliminar este producto")
    
    # Eliminar el detalle del carrito
    db.delete(detalle)
    db.commit()
    
    # Redirigir de vuelta al carrito
    return RedirectResponse(url="/tienda/carrito", status_code=303)


@router.post("/tienda/carrito/actualizar/{detalle_id}")
def actualizar_carrito(
    request: Request,
    detalle_id: int,
    cantidad: int = Form(...),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(current_active_user)
):
    # Validar cantidad
    if cantidad < 1:
        raise HTTPException(status_code=400, detail="La cantidad debe ser mayor a 0")
    
    # Buscar el detalle del carrito
    detalle = db.query(CarritoDetalle).filter(CarritoDetalle.id == detalle_id).first()
    
    if not detalle:
        raise HTTPException(status_code=404, detail="Producto no encontrado en el carrito")
    
    # Verificar que el carrito pertenece al usuario actual
    carrito = db.query(Carrito).filter(
        Carrito.id == detalle.carrito_id,
        Carrito.usuario_id == usuario.id
    ).first()
    
    if not carrito:
        raise HTTPException(status_code=403, detail="No tienes permisos para actualizar este producto")
    
    # Actualizar la cantidad
    detalle.cantidad = cantidad
    db.commit()
    
    # Redirigir de vuelta al carrito
    return RedirectResponse(url="/tienda/carrito", status_code=303)


@router.get("/tienda/pago", response_class=HTMLResponse)
def pago(request: Request, db: Session = Depends(get_db), usuario: Usuario = Depends(current_active_user)):
    # Buscar el carrito activo del usuario
    carrito = db.query(Carrito).filter(Carrito.usuario_id == usuario.id, Carrito.estado == "activo").first()
    
    if not carrito:
        return RedirectResponse(url="/tienda/carrito", status_code=303)
    
    # Obtener los detalles del carrito
    detalles = db.query(CarritoDetalle).filter(CarritoDetalle.carrito_id == carrito.id).all()
    
    if not detalles:
        return RedirectResponse(url="/tienda/carrito", status_code=303)
    
    # Calcular totales con descuentos
    total_original = 0
    total_con_descuentos = 0
    total_descuentos = 0
    cantidad_total_productos = sum(detalle.cantidad for detalle in detalles)
    
    for detalle in detalles:
        # Cargar producto con promociones
        producto = db.query(Producto).options(
            joinedload(Producto.promociones).joinedload(PromocionProducto.promocion)
        ).filter(Producto.id == detalle.producto_id).first()
        
        # Buscar promoción activa
        promocion_activa = None
        for pp in producto.promociones:
            if pp.promocion.activo and pp.promocion.fecha_inicio.date() <= date.today() <= pp.promocion.fecha_fin.date():
                promocion_activa = pp.promocion
                break
        
        # Calcular precios
        precio_original = producto.precio
        if promocion_activa:
            if promocion_activa.tipo_descuento == 'porcentaje':
                precio_con_descuento = precio_original * (1 - promocion_activa.valor / 100)
            else:
                precio_con_descuento = max(0, precio_original - promocion_activa.valor)
            producto.precio_con_descuento = precio_con_descuento
            producto.promocion_activa = promocion_activa
        else:
            precio_con_descuento = precio_original
            producto.precio_con_descuento = precio_con_descuento
            producto.promocion_activa = None
        
        # Calcular subtotales
        subtotal_original = precio_original * detalle.cantidad
        subtotal_con_descuento = precio_con_descuento * detalle.cantidad
        descuento_aplicado = subtotal_original - subtotal_con_descuento
        
        # Agregar datos al detalle para el template
        detalle.producto = producto
        detalle.subtotal_original = subtotal_original
        detalle.subtotal_con_descuento = subtotal_con_descuento
        detalle.descuento_aplicado = descuento_aplicado
        
        # Sumar a totales
        total_original += subtotal_original
        total_con_descuentos += subtotal_con_descuento
        total_descuentos += descuento_aplicado
    
    total_carrito = total_con_descuentos
    
    # Obtener direcciones del usuario
    direcciones = db.query(Direccion).filter(Direccion.usuario_id == usuario.id).all()
    
    # Asignar los detalles al carrito
    carrito.detalle = detalles
    
    return templates.TemplateResponse("pago.html", {
        "request": request,
        "carrito": carrito,
        "detalles": detalles,
        "total_carrito": total_carrito,
        "total_original": total_original,
        "total_descuentos": total_descuentos,
        "cantidad_total_productos": cantidad_total_productos,
        "direcciones": direcciones
    })


@router.post("/tienda/pago/direccion")
def guardar_direccion(
    request: Request,
    direccion: str = Form(...),
    detalle: str = Form(""),
    ciudad: str = Form(...),
    departamento: str = Form(...),
    codigo_postal: str = Form(""),
    tipo: str = Form("Casa"),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(current_active_user)
):
    # Crear nueva dirección
    nueva_direccion = Direccion(
        usuario_id=usuario.id,
        direccion=direccion,
        detalle=detalle if detalle else None,
        ciudad=ciudad,
        departamento=departamento,
        codigo_postal=codigo_postal if codigo_postal else None,
        pais="Uruguay",
        tipo=tipo
    )
    
    db.add(nueva_direccion)
    db.commit()
    
    return RedirectResponse(url="/tienda/pago", status_code=303)


@router.post("/tienda/pago/procesar")
def procesar_pago(
    request: Request,
    direccion_id: Optional[int] = Form(None),
    direccion: Optional[str] = Form(None),
    detalle: Optional[str] = Form(None),
    ciudad: Optional[str] = Form(None),
    departamento: Optional[str] = Form(None),
    codigo_postal: Optional[str] = Form(None),
    tipo: Optional[str] = Form(None),
    codigo_cupon: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(current_active_user),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    # Buscar el carrito activo del usuario
    carrito = db.query(Carrito).filter(Carrito.usuario_id == usuario.id, Carrito.estado == "activo").first()
    
    if not carrito:
        return RedirectResponse(url="/tienda/carrito", status_code=303)
    
    # Obtener los detalles del carrito
    detalles = db.query(CarritoDetalle).filter(CarritoDetalle.carrito_id == carrito.id).all()
    
    if not detalles:
        return RedirectResponse(url="/tienda/carrito", status_code=303)
    
    # Calcular totales con descuentos
    total_productos = 0
    descuento_cupon = 0
    
    for detalle in detalles:
        # Cargar producto con promociones
        producto = db.query(Producto).options(
            joinedload(Producto.promociones).joinedload(PromocionProducto.promocion)
        ).filter(Producto.id == detalle.producto_id).first()
        
        # Buscar promoción activa
        promocion_activa = None
        for pp in producto.promociones:
            if pp.promocion.activo and pp.promocion.fecha_inicio.date() <= date.today() <= pp.promocion.fecha_fin.date():
                promocion_activa = pp.promocion
                break
        
        # Calcular precio con descuento
        precio_original = producto.precio
        if promocion_activa:
            if promocion_activa.tipo_descuento == 'porcentaje':
                precio_con_descuento = precio_original * (1 - promocion_activa.valor / 100)
            else:
                precio_con_descuento = max(0, precio_original - promocion_activa.valor)
        else:
            precio_con_descuento = precio_original
        
        total_productos += precio_con_descuento * detalle.cantidad
    
    # Aplicar cupón si existe
    if codigo_cupon and codigo_cupon.strip():
        cupon = db.query(Cupon).filter(
            Cupon.codigo == codigo_cupon.strip().upper(),
            Cupon.activo == True
        ).first()
        
        if cupon:
            # Verificar fechas y uso previo
            fecha_actual = datetime.now()
            if (fecha_actual >= cupon.fecha_inicio and 
                fecha_actual <= cupon.fecha_fin):
                
                uso_previo = db.query(CuponUso).filter(
                    CuponUso.cupon_id == cupon.id,
                    CuponUso.usuario_id == usuario.id
                ).first()
                
                if not uso_previo:
                    # Calcular descuento del cupón
                    if cupon.tipo_descuento == "porcentaje":
                        descuento_cupon = total_productos * (cupon.valor / 100)
                    else:
                        descuento_cupon = min(cupon.valor, total_productos)
    
    total_final = total_productos - descuento_cupon
    
    # Obtener o crear dirección de envío
    direccion_envio = None
    costo_envio = 0
    
    if direccion_id:
        # Usar dirección existente
        direccion_envio = db.query(Direccion).filter(
            Direccion.id == direccion_id, 
            Direccion.usuario_id == usuario.id
        ).first()
    elif direccion and ciudad and departamento:
        # Crear nueva dirección
        direccion_envio = Direccion(
            usuario_id=usuario.id,
            direccion=direccion,
            detalle=detalle,
            ciudad=ciudad,
            departamento=departamento,
            codigo_postal=codigo_postal if codigo_postal else None,
            pais="Uruguay",
            tipo=tipo
        )
        db.add(direccion_envio)
        db.commit()
        db.refresh(direccion_envio)
    
    # Validar que tenemos una dirección
    if not direccion_envio:
        return RedirectResponse(url="/tienda/pago?error=direccion_requerida", status_code=303)
    
    # Calcular costo de envío desde la base de datos
    from app.models.costos_envio import CostoEnvio
    costo_envio_db = db.query(CostoEnvio).filter(
        CostoEnvio.departamento == direccion_envio.departamento,
        CostoEnvio.activo == True
    ).first()
    
    if costo_envio_db:
        costo_envio = costo_envio_db.costo
    else:
        costo_envio = 0
    
    total_con_envio = total_final + costo_envio
    
    # Crear la orden
    nueva_orden = Orden(
        usuario_id=usuario.id,
        direccion_envio_id=direccion_envio.id,
        total=total_productos,
        estado="pendiente",
        metodo_pago='mercadopago',
        descuento_total=descuento_cupon,
        costo_envio=costo_envio,
        total_final=total_con_envio
    )
    
    db.add(nueva_orden)
    db.commit()
    db.refresh(nueva_orden)
    
    # Crear los detalles de la orden
    for detalle in detalles:
        # Cargar producto con promociones para precio correcto
        producto = db.query(Producto).options(
            joinedload(Producto.promociones).joinedload(PromocionProducto.promocion)
        ).filter(Producto.id == detalle.producto_id).first()
        
        # Calcular precio unitario con descuento
        precio_unitario = producto.precio
        for pp in producto.promociones:
            if pp.promocion.activo and pp.promocion.fecha_inicio.date() <= date.today() <= pp.promocion.fecha_fin.date():
                if pp.promocion.tipo_descuento == 'porcentaje':
                    precio_unitario = producto.precio * (1 - pp.promocion.valor / 100)
                else:
                    precio_unitario = max(0, producto.precio - pp.promocion.valor)
                break
        
        orden_detalle = OrdenDetalle(
            orden_id=nueva_orden.id,
            producto_id=detalle.producto_id,
            cantidad=detalle.cantidad,
            precio_unitario=precio_unitario
        )
        db.add(orden_detalle)
    
    db.commit()
    
    # Crear item único para MercadoPago con el total de la compra
    items = [{
        "title": f"Compra en Santolina - Orden #{nueva_orden.id}",
        "quantity": 1,
        "unit_price": float(total_con_envio),
        "currency_id": "UYU"
    }]
    
    # Crear preferencia de pago
    sdk = mercadopago.SDK(os.getenv("MERCADO_PAGO_ACCESS_TOKEN"))
    preference_data = {
        "items": items,
        "payer": {
            "name": usuario.nombre,
            "email": usuario.email,
        },
        "back_urls": {
            "success": f"{base_url}/tienda/pago-exitoso?orden_id={nueva_orden.id}",
            "failure": f"{base_url}/tienda/pago-error",
            "pending": f"{base_url}/tienda/pago-pendiente?orden_id={nueva_orden.id}"
        },
        "auto_return": "approved",
        "external_reference": f"ORD{nueva_orden.id}",
        "notification_url": f"{base_url}/webhooks/mercadopago"
    }
    
    preference_response = sdk.preference().create(preference_data)
    preference = preference_response["response"]
    
    return RedirectResponse(url=preference["init_point"], status_code=303)


@router.post("/tienda/validar-cupon")
async def validar_cupon(request: Request, db: Session = Depends(get_db), usuario: Usuario = Depends(current_active_user)):
    """Validar un cupón de descuento"""
    try:
        body = await request.json()
        codigo = body.get("codigo", "").strip().upper()
        total = float(body.get("total", 0))
        
        if not codigo:
            return {"valido": False, "mensaje": "Código de cupón requerido"}
        
        # Buscar el cupón
        cupon = db.query(Cupon).filter(
            Cupon.codigo == codigo,
            Cupon.activo == True
        ).first()
        
        if not cupon:
            return {"valido": False, "mensaje": "Código de cupón inválido"}
        
        # Verificar fechas de validez
        fecha_actual = datetime.now()
        if fecha_actual < cupon.fecha_inicio:
            return {"valido": False, "mensaje": "Este cupón aún no está disponible"}
        
        if fecha_actual > cupon.fecha_fin:
            return {"valido": False, "mensaje": "Este cupón ha expirado"}
        
        # Verificar si el usuario ya usó este cupón
        uso_previo = db.query(CuponUso).filter(
            CuponUso.cupon_id == cupon.id,
            CuponUso.usuario_id == usuario.id
        ).first()
        
        if uso_previo:
            return {"valido": False, "mensaje": "Ya has usado este cupón anteriormente"}
        
        # Calcular descuento
        if cupon.tipo_descuento == "porcentaje":
            descuento = total * (cupon.valor / 100)
            mensaje = f"Cupón aplicado: {cupon.valor}% de descuento"
        else:
            descuento = min(cupon.valor, total)  # No puede ser mayor al total
            mensaje = f"Cupón aplicado: ${cupon.valor} de descuento"
        
        return {
            "valido": True,
            "mensaje": mensaje,
            "cupon": {
                "id": cupon.id,
                "codigo": cupon.codigo,
                "descripcion": cupon.descripcion,
                "tipo_descuento": cupon.tipo_descuento,
                "valor": cupon.valor
            },
            "descuento": round(descuento, 2)
        }
        
    except Exception as e:
        return {"valido": False, "mensaje": "Error al validar el cupón"}


@router.get("/tienda/pago-exitoso")
def pago_exitoso_tienda(
    request: Request,
    orden_id: int,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    orden = db.query(Orden).filter(Orden.id == orden_id).first()
    if not orden:
        return RedirectResponse(url="/tienda", status_code=303)
    
    # Cambiar estado de la orden a pagado
    orden.estado = "pagado"
    db.commit()
    
    # Cambiar estado del carrito a completado
    carrito = db.query(Carrito).filter(Carrito.usuario_id == orden.usuario_id, Carrito.estado == "activo").first()
    if carrito:
        carrito.estado = "completado"
        db.commit()
    
    # Cargar relaciones necesarias para los emails
    orden = db.query(Orden).options(
        joinedload(Orden.detalle).joinedload(OrdenDetalle.producto),
        joinedload(Orden.usuario),
        joinedload(Orden.direccion_envio)
    ).get(orden.id)
    
    # Enviar emails de confirmación
    background_tasks.add_task(enviar_confirmacion_orden, orden, orden.usuario)
    background_tasks.add_task(notificar_admin_orden, orden, orden.usuario)
    
    return templates.TemplateResponse("pago_exitoso_tienda.html", {
        "request": request,
        "orden": orden
    })


@router.get("/tienda/pago-error")
def pago_error_tienda(request: Request):
    return templates.TemplateResponse("pago_error.html", {
        "request": request,
        "mensaje": "Hubo un problema con el pago. Por favor, intenta nuevamente."
    })


@router.get("/tienda/pago-pendiente")
def pago_pendiente_tienda(
    request: Request,
    orden_id: int,
    db: Session = Depends(get_db)
):
    orden = db.query(Orden).filter(Orden.id == orden_id).first()
    if not orden:
        return RedirectResponse(url="/tienda", status_code=303)
    
    # Actualizar estado si está pendiente
    if orden.estado == "pendiente":
        orden.estado = "en_proceso"
        db.commit()
    
    return templates.TemplateResponse("pago_pendiente.html", {
        "request": request,
        "orden": orden,
        "mensaje": "Tu pago está siendo procesado. Te notificaremos cuando se complete."
    })


@router.get("/tienda/costo-envio/{departamento}")
def obtener_costo_envio(
    departamento: str,
    db: Session = Depends(get_db)
):
    """Obtiene el costo de envío para un departamento específico"""
    costo_envio = db.query(CostoEnvio).filter(
        CostoEnvio.departamento == departamento,
        CostoEnvio.activo == True
    ).first()
    
    if costo_envio:
        return {"costo": costo_envio.costo}
    else:
        return {"costo": 0}