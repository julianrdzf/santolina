from fastapi import APIRouter, Request, Depends, UploadFile, File, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models.evento import Evento
from app.models.categorias import Categoria
from app.models.reserva import Reserva
from app.models.categorias_productos import CategoriaProducto
from app.models.productos import Producto
from app.models.imagenes_productos import ImagenProducto
from app.models.promocion_productos import PromocionProducto
from app.models.promociones import Promocion
from app.models.cupones import Cupon
from app.models.cupones_uso import CuponUso

from fastapi import Form
from fastapi.responses import RedirectResponse, JSONResponse

from app.routers.auth import current_superuser
from typing import Optional, List
from datetime import datetime

import cloudinary.uploader


router = APIRouter()
templates = Jinja2Templates(directory="frontend/templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/admin", dependencies=[Depends(current_superuser)])
def admin_home(request: Request):
    return templates.TemplateResponse("admin_panel.html", {"request": request})

@router.get("/admin/eventos", dependencies=[Depends(current_superuser)])
def listar_eventos_admin(request: Request, db: Session = Depends(get_db)):
    eventos = db.query(Evento).all()
    return templates.TemplateResponse("admin_eventos.html", {
        "request": request,
        "eventos": eventos
    })

@router.get("/admin/eventos/crear", dependencies=[Depends(current_superuser)])
def mostrar_formulario_crear_evento(request: Request, db: Session = Depends(get_db)):
    categorias = db.query(Categoria).all()
    return templates.TemplateResponse("admin_evento_form.html", {
        "request": request,
        "categorias": categorias,
        "modo": "crear"
    })

@router.post("/admin/eventos/crear", dependencies=[Depends(current_superuser)])
def crear_evento(
    titulo: str = Form(...),
    descripcion: str = Form(...),
    fecha: str = Form(...),
    cupos: int = Form(...),
    categoria_id: Optional[str] = Form(None),
    horario: str = Form(None),
    ubicacion: str = Form(None),
    direccion: str = Form(None),
    costo: float = Form(...),
    db: Session = Depends(get_db)
):
    
    # Si vino vacío, lo convierto a None
    categoria_id_int = int(categoria_id) if categoria_id else None

    nuevo_evento = Evento(
        titulo=titulo,
        descripcion=descripcion,
        fecha=fecha,
        cupos_totales=cupos,
        categoria_id=categoria_id_int,
        hora=horario,
        ubicacion=ubicacion,
        direccion=direccion,
        costo=costo
    )
    db.add(nuevo_evento)
    db.commit()
    return RedirectResponse(url="/admin/eventos", status_code=303)

@router.get("/admin/eventos/{evento_id}/editar", dependencies=[Depends(current_superuser)])
def mostrar_formulario_editar_evento(evento_id: int, request: Request, db: Session = Depends(get_db)):
    evento = db.query(Evento).get(evento_id)
    categorias = db.query(Categoria).all()
    if not evento:
        return templates.TemplateResponse("404.html", {"request": request})
    
    return templates.TemplateResponse("admin_evento_form.html", {
        "request": request,
        "evento": evento,
        "categorias": categorias,
        "modo": "editar"
    })

@router.post("/admin/eventos/{evento_id}/editar", dependencies=[Depends(current_superuser)])
def actualizar_evento(
    evento_id: int,
    titulo: str = Form(...),
    descripcion: str = Form(...),
    fecha: str = Form(...),
    cupos: int = Form(...),
    categoria_id: Optional[str] = Form(None),
    horario: str = Form(None),
    ubicacion: str = Form(None),
    costo: float = Form(...),
    db: Session = Depends(get_db)
):
    # Si vino vacío, lo convierto a None
    categoria_id_int = int(categoria_id) if categoria_id else None

    evento = db.query(Evento).get(evento_id)
    if not evento:
        return RedirectResponse(url="/admin/eventos", status_code=303)

    evento.titulo = titulo
    evento.descripcion = descripcion
    evento.fecha = fecha
    evento.cupos_totales = cupos
    evento.categoria_id = categoria_id_int
    evento.horario = horario
    evento.ubicacion = ubicacion
    evento.costo = costo

    db.commit()
    return RedirectResponse(url="/admin/eventos", status_code=303)

@router.get("/admin/eventos/{evento_id}/clonar", dependencies=[Depends(current_superuser)])
def mostrar_formulario_clonar_evento(evento_id: int, request: Request, db: Session = Depends(get_db)):
    evento = db.query(Evento).get(evento_id)
    categorias = db.query(Categoria).all()
    if not evento:
        return templates.TemplateResponse("404.html", {"request": request})
    
    return templates.TemplateResponse("admin_evento_form.html", {
        "request": request,
        "evento": evento,
        "categorias": categorias,
        "modo": "clonar"
    })

@router.post("/admin/eventos/{evento_id}/eliminar", dependencies=[Depends(current_superuser)])
def eliminar_evento(evento_id: int, db: Session = Depends(get_db)):
    evento = db.query(Evento).get(evento_id)
    if evento:
        if evento.reservas:
            return templates.TemplateResponse("error_admin.html", {
                "request": {},  # o pasá request si usás plantilla con jinja
                "mensaje": "No se puede eliminar el evento porque tiene reservas registradas.",
                "url_volver": "/admin/eventos"
            })
        db.delete(evento)
        db.commit()
    return RedirectResponse(url="/admin/eventos", status_code=303)

@router.get("/admin/eventos/{evento_id}/reservas", dependencies=[Depends(current_superuser)])
def ver_reservas_evento(evento_id: int, request: Request, db: Session = Depends(get_db)):
    evento = db.query(Evento).get(evento_id)
    if not evento:
        return RedirectResponse(url="/admin/eventos", status_code=303)
    
    reservas = evento.reservas  # gracias a la relación ya definida
    return templates.TemplateResponse("admin_reservas_evento.html", {
        "request": request,
        "evento": evento,
        "reservas": reservas
    })

@router.post("/admin/reservas/{reserva_id}/eliminar", dependencies=[Depends(current_superuser)])
def eliminar_reserva(reserva_id: int, db: Session = Depends(get_db)):
    reserva = db.query(Reserva).get(reserva_id)
    if reserva:
        evento_id = reserva.evento_id  # para redirigir luego
        db.delete(reserva)
        db.commit()
        return RedirectResponse(f"/admin/eventos/{evento_id}/reservas", status_code=303)
    return RedirectResponse("/admin/eventos", status_code=303)



#################################
# Tienda
#####################

#############################
# Categorias

@router.get("/admin/tienda-panel", dependencies=[Depends(current_superuser)])
def admin_home(request: Request):
    return templates.TemplateResponse("admin_tienda_panel.html", {"request": request})


# Listar categorías de productos
@router.get("/admin/categorias_productos", dependencies=[Depends(current_superuser)])
def listar_categorias_productos(request: Request, db: Session = Depends(get_db)):
    categorias = db.query(CategoriaProducto).all()
    return templates.TemplateResponse("admin_categorias_productos.html", {
        "request": request,
        "categorias": categorias
    })

@router.get("/admin/categorias_productos/padres", dependencies=[Depends(current_superuser)])
def listar_categorias_padres(request: Request, db: Session = Depends(get_db)):
    # Filtramos solo las categorías que no tienen padre
    categorias_padres = db.query(CategoriaProducto).filter(CategoriaProducto.id_categoria_padre == None).all()

    return templates.TemplateResponse("admin_categorias_productos.html", {
        "request": request,
        "categorias": categorias_padres,
        "titulo": "Categorías principales"
    })

@router.get("/admin/categorias/{categoria_id}/hijos", dependencies=[Depends(current_superuser)])
def listar_hijos_categoria(categoria_id: int, request: Request, db: Session = Depends(get_db)):
    # Buscamos la categoría padre
    categoria_padre = db.query(CategoriaProducto).get(categoria_id)
    if not categoria_padre:
        return templates.TemplateResponse("404.html", {"request": request})

    # Tomamos solo las subcategorías
    subcategorias = categoria_padre.subcategorias

    return templates.TemplateResponse("admin_categorias_productos.html", {
        "request": request,
        "categorias": subcategorias,
        "categoria_padre": categoria_padre
    })

# Mostrar formulario crear categoría
@router.get("/admin/categorias_productos/crear", dependencies=[Depends(current_superuser)])
def mostrar_formulario_crear_categoria_producto(request: Request, db: Session = Depends(get_db)):
    categorias = db.query(CategoriaProducto).all()  # para seleccionar padre opcional
    return templates.TemplateResponse("admin_categoria_producto_form.html", {
        "request": request,
        "categorias": categorias,
        "modo": "crear"
    })

# Crear categoría
@router.post("/admin/categorias_productos/crear", dependencies=[Depends(current_superuser)])
def crear_categoria_producto(
    nombre: str = Form(...), 
    id_categoria_padre: Optional[str] = Form(None), 
    db: Session = Depends(get_db)
):
    # Si vino vacío, lo convierto a None
    id_categoria_padre = int(id_categoria_padre) if id_categoria_padre else None

    if id_categoria_padre is not None:
        padre = db.query(CategoriaProducto).get(id_categoria_padre)
        if not padre:
            return templates.TemplateResponse("error_admin.html", {
                "request": {},
                "mensaje": "La categoría padre seleccionada no existe.",
                "url_volver": "/admin/categorias_productos"
            })
    
    nueva_categoria = CategoriaProducto(
        nombre=nombre,
        id_categoria_padre=id_categoria_padre
    )
    db.add(nueva_categoria)
    db.commit()
    return RedirectResponse(url="/admin/categorias_productos", status_code=303)

# Mostrar formulario editar categoría
@router.get("/admin/categorias_productos/{categoria_id}/editar", dependencies=[Depends(current_superuser)])
def mostrar_formulario_editar_categoria_producto(categoria_id: int, request: Request, db: Session = Depends(get_db)):
    categoria = db.query(CategoriaProducto).get(categoria_id)
    if not categoria:
        return templates.TemplateResponse("404.html", {"request": request})
    categorias = db.query(CategoriaProducto).filter(CategoriaProducto.id != categoria_id).all()
    return templates.TemplateResponse("admin_categoria_producto_form.html", {
        "request": request,
        "categoria": categoria,
        "categorias": categorias,
        "modo": "editar"
    })

# Actualizar categoría
@router.post("/admin/categorias_productos/{categoria_id}/editar", dependencies=[Depends(current_superuser)])
def actualizar_categoria_producto(
    categoria_id: int, 
    nombre: str = Form(...), 
    id_categoria_padre: Optional[str] = Form(None), 
    db: Session = Depends(get_db)
):
    # Si vino vacío, lo convierto a None
    id_categoria_padre = int(id_categoria_padre) if id_categoria_padre else None

    categoria = db.query(CategoriaProducto).get(categoria_id)
    if not categoria:
        return RedirectResponse(url="/admin/categorias_productos", status_code=303)

    if id_categoria_padre == categoria.id:
        return templates.TemplateResponse("error_admin.html", {
            "request": {},
            "mensaje": "Una categoría no puede ser padre de sí misma."
        })

    # Validar que no haya ciclo en ancestros
    ancestro_id = id_categoria_padre
    while ancestro_id:
        if ancestro_id == categoria.id:
            return templates.TemplateResponse("error_admin.html", {
                "request": {},
                "mensaje": "No se puede crear un ciclo en la jerarquía de categorías.",
                "url_volver": "/admin/categorias_productos"
            })
        ancestro = db.query(CategoriaProducto).get(ancestro_id)
        ancestro_id = ancestro.id_categoria_padre if ancestro else None

    categoria.nombre = nombre
    categoria.id_categoria_padre = id_categoria_padre
    db.commit()
    return RedirectResponse(url="/admin/categorias_productos", status_code=303)

@router.post("/admin/categorias_productos/{categoria_id}/eliminar", dependencies=[Depends(current_superuser)])
def eliminar_categoria_producto(categoria_id: int, db: Session = Depends(get_db)):
    categoria = db.query(CategoriaProducto).get(categoria_id)
    if categoria:
        # Verificar si tiene subcategorías
        hijos = db.query(CategoriaProducto).filter(CategoriaProducto.id_categoria_padre == categoria_id).all()
        if hijos:
            return templates.TemplateResponse("error_admin.html", {
                "request": {},
                "mensaje": "No se puede eliminar la categoría porque tiene subcategorías asociadas.",
                "url_volver": "/admin/categorias_productos"
            })

        # Verificar si tiene productos asociados
        productos = db.query(Producto).filter(Producto.id_categoria == categoria_id).all()
        if productos:
            return templates.TemplateResponse("error_admin.html", {
                "request": {},
                "mensaje": "No se puede eliminar la categoría porque tiene productos asociados.",
                "url_volver": "/admin/categorias_productos"
            })

        db.delete(categoria)
        db.commit()
    return RedirectResponse(url="/admin/categorias_productos", status_code=303)


###########################
# Productos

@router.get("/admin/productos", dependencies=[Depends(current_superuser)])
def listar_productos(request: Request, db: Session = Depends(get_db)):
    productos = db.query(Producto).all()
    return templates.TemplateResponse("admin_productos.html", {
        "request": request,
        "productos": productos
    })


@router.get("/admin/productos/crear", dependencies=[Depends(current_superuser)])
def mostrar_formulario_crear_producto(request: Request, db: Session = Depends(get_db)):
    categorias = db.query(CategoriaProducto).all()
    return templates.TemplateResponse("admin_producto_form.html", {
        "request": request,
        "categorias": categorias,
        "modo": "crear"
    })


@router.post("/admin/productos/crear", dependencies=[Depends(current_superuser)])
def crear_producto(
    nombre: str = Form(...),
    descripcion: str = Form(None),
    precio: float = Form(...),
    stock: int = Form(...),
    id_categoria: Optional[str] = Form(None),
    imagen1: UploadFile = File(None),
    imagen2: UploadFile = File(None),
    imagen3: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    id_categoria = int(id_categoria) if id_categoria else None
    nuevo_producto = Producto(
        nombre=nombre,
        descripcion=descripcion,
        precio=precio,
        stock=stock,
        id_categoria=id_categoria
    )
    db.add(nuevo_producto)
    db.commit()
    db.refresh(nuevo_producto)

    for imagen in [imagen1, imagen2, imagen3]:
        if imagen and imagen.filename:
            # Subimos la imagen con transformaciones
            result = cloudinary.uploader.upload(
                imagen.file,
                folder="productos",             # Carpeta en Cloudinary
                transformation=[
                    {"width": 1200, "height": 1200, "crop": "limit"},  # Limita lado más largo a 1200px
                    {"quality": "auto"},                               # Calidad automática
                    {"fetch_format": "auto"}                           # WebP/avif según navegador
                ]
            )
            url = result.get("secure_url")
            public_id = result.get("public_id")
            nueva_imagen = ImagenProducto(
                id_producto=nuevo_producto.id,
                url_imagen=url,
                public_id=public_id,
                descripcion=None
            )
            db.add(nueva_imagen)
    db.commit()

    return RedirectResponse("/admin/productos", status_code=303)


@router.get("/admin/productos/{producto_id}/editar", dependencies=[Depends(current_superuser)])
def mostrar_formulario_editar_producto(producto_id: int, request: Request, db: Session = Depends(get_db)):
    producto = db.query(Producto).get(producto_id)
    categorias = db.query(CategoriaProducto).all()
    if not producto:
        return templates.TemplateResponse("404.html", {"request": request})
    return templates.TemplateResponse("admin_producto_form.html", {
        "request": request,
        "producto": producto,
        "categorias": categorias,
        "modo": "editar"
    })


@router.post("/admin/productos/{producto_id}/editar", dependencies=[Depends(current_superuser)])
def actualizar_producto(
    producto_id: int,
    nombre: str = Form(...),
    descripcion: str = Form(None),
    precio: float = Form(...),
    stock: int = Form(...),
    id_categoria: Optional[str] = Form(None),
    imagen1: UploadFile = File(None),
    imagen2: UploadFile = File(None),
    imagen3: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    id_categoria = int(id_categoria) if id_categoria else None

    producto = db.query(Producto).get(producto_id)
    if not producto:
        return RedirectResponse("/admin/productos", status_code=303)

    # Actualizar datos base
    producto.nombre = nombre
    producto.descripcion = descripcion
    producto.precio = precio
    producto.stock = stock
    producto.id_categoria = id_categoria

    # Manejo de imágenes (máx 3)
    imagenes_archivos = [imagen1, imagen2, imagen3]

    for i, imagen_file in enumerate(imagenes_archivos):
        if imagen_file and imagen_file.filename:            
            # Subimos la imagen con transformaciones
            upload_result = cloudinary.uploader.upload(
                imagen_file.file,
                folder="productos",             # Carpeta en Cloudinary
                transformation=[
                    {"width": 1200, "height": 1200, "crop": "limit"},  # Limita lado más largo a 1200px
                    {"quality": "auto"},                               # Calidad automática
                    {"fetch_format": "auto"}                           # WebP/avif según navegador
                ]
            )
            url = upload_result["secure_url"]

            if i < len(producto.imagenes):
                old_img = producto.imagenes[i]
                # eliminar de cloudinary si hay una anterior
                if old_img.public_id:
                    cloudinary.uploader.destroy(old_img.public_id)
                # actualizar con la nueva
                old_img.url_imagen = url
                old_img.public_id = upload_result["public_id"]
            else:
                nueva_img = ImagenProducto(
                    id_producto=producto.id,
                    url_imagen=url,
                    public_id=upload_result["public_id"]
                )
                db.add(nueva_img)

    db.commit()
    return RedirectResponse("/admin/productos", status_code=303)


@router.post("/admin/productos/{producto_id}/eliminar", dependencies=[Depends(current_superuser)])
def eliminar_producto(producto_id: int, db: Session = Depends(get_db)):
    producto = db.query(Producto).get(producto_id)
    if producto:
        # 1. Obtener todas las imágenes del producto
        imagenes = db.query(ImagenProducto).filter(ImagenProducto.id_producto == producto.id).all()

        # 2. Eliminar de Cloudinary
        for img in imagenes:
            if img.public_id:
                try:
                    cloudinary.uploader.destroy(img.public_id)
                except Exception as e:
                    print(f"No se pudo eliminar la imagen {img.public_id}: {e}")

        # 3. Eliminar las filas de imagen en la DB
        for img in imagenes:
            db.delete(img)

        # 4. Finalmente, eliminar el producto
        db.delete(producto)
        db.commit()

    return RedirectResponse("/admin/productos", status_code=303)

@router.post("/admin/productos/eliminar_imagen/{imagen_id}", dependencies=[Depends(current_superuser)])
def eliminar_imagen_producto(imagen_id: int, db: Session = Depends(get_db)):
    # Buscar la imagen en la base de datos
    imagen = db.query(ImagenProducto).get(imagen_id)
    if not imagen:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")

    # Si tenemos public_id de Cloudinary, eliminar de allí
    if hasattr(imagen, "public_id") and imagen.public_id:
        try:
            cloudinary.uploader.destroy(imagen.public_id)
        except Exception as e:
            print("Error eliminando de Cloudinary:", e)
            # Podemos decidir si continuar o abortar; aquí continuamos

    # Eliminar registro en la base de datos
    db.delete(imagen)
    db.commit()

    return JSONResponse({"success": True, "message": "Imagen eliminada"})


###########################
# Promociones

@router.get("/admin/promociones", dependencies=[Depends(current_superuser)])
def listar_promociones(db: Session = Depends(get_db)):
    promociones = db.query(Promocion).all()
    return templates.TemplateResponse(
        "admin_promociones.html",
        {
            "request": {},
            "promociones": promociones
        }
    )

@router.get("/admin/promociones/crear", dependencies=[Depends(current_superuser)])
def form_crear_promocion(request: Request):
    return templates.TemplateResponse(
        "admin_promocion_form.html",
        {"request": request, "modo": "crear"}
    )

@router.post("/admin/promociones/crear", dependencies=[Depends(current_superuser)])
def crear_promocion(
    titulo: str = Form(...),
    descripcion: str = Form(None),
    tipo_descuento: str = Form(None),
    valor: float = Form(...),
    fecha_inicio: str = Form(...),
    fecha_fin: str = Form(...),
    activo: Optional[str] = Form(None),  # Checkbox
    productos: Optional[List[int]] = Form(None),  # IDs de productos seleccionados
    db: Session = Depends(get_db)
):
    nueva_promocion = Promocion(
        titulo=titulo,
        descripcion=descripcion,
        tipo_descuento='porcentaje',
        valor=valor,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        activo=True if activo == "on" else False 
    )
    db.add(nueva_promocion)
    db.commit()
    db.refresh(nueva_promocion)

    # Asociar productos
    if productos:
        for prod_id in productos:
            db.add(PromocionProducto(id_promocion=nueva_promocion.id, id_producto=prod_id))
        db.commit()

    return RedirectResponse("/admin/promociones", status_code=303)


@router.get("/admin/promociones/{promo_id}/editar", dependencies=[Depends(current_superuser)])
def form_editar_promocion(promo_id: int, request: Request, db: Session = Depends(get_db)):
    promocion = db.query(Promocion).get(promo_id)
    if not promocion:
        return RedirectResponse("/admin/promociones", status_code=303)
    
    return templates.TemplateResponse(
        "admin_promocion_form.html",
        {"request": request, "modo": "editar", "promocion": promocion}
    )

@router.post("/admin/promociones/{promocion_id}/editar", dependencies=[Depends(current_superuser)])
def editar_promocion(
    promocion_id: int,
    titulo: str = Form(...),
    descripcion: str = Form(None),
    tipo_descuento: str = Form(None),
    valor: float = Form(...),
    fecha_inicio: str = Form(...),
    fecha_fin: str = Form(...),
    activo: Optional[str] = Form(None),  # Checkbox
    productos: Optional[List[int]] = Form(None),
    db: Session = Depends(get_db)
):
    promocion = db.query(Promocion).get(promocion_id)
    if not promocion:
        return RedirectResponse("/admin/promociones", status_code=303)

    promocion.titulo = titulo
    promocion.descripcion = descripcion    
    promocion.valor = valor
    promocion.fecha_inicio = datetime.fromisoformat(fecha_inicio)
    promocion.fecha_fin = datetime.fromisoformat(fecha_fin)
    promocion.activo = True if activo == "on" else False 

    # Actualizar productos asociados
    db.query(PromocionProducto).filter(PromocionProducto.id_promocion == promocion_id).delete()
    if productos:
        for prod_id in productos:
            db.add(PromocionProducto(id_promocion=promocion_id, id_producto=prod_id))

    db.commit()
    return RedirectResponse("/admin/promociones", status_code=303)

@router.post("/admin/promociones/{promo_id}/eliminar", dependencies=[Depends(current_superuser)])
def eliminar_promocion(promo_id: int, db: Session = Depends(get_db)):
    promocion = db.query(Promocion).get(promo_id)
    if promocion:
        # Eliminar relaciones con productos primero
        if promocion.productos:
            for rel in promocion.productos:
                db.delete(rel)
        
        # Luego eliminar la promoción
        db.delete(promocion)
        db.commit()
    
    return RedirectResponse("/admin/promociones", status_code=303)


###################################
# Cupones

# Listado
@router.get("/admin/cupones", dependencies=[Depends(current_superuser)])
def listar_cupones(request: Request, db: Session = Depends(get_db)):
    cupones = db.query(Cupon).all()
    return templates.TemplateResponse("admin_cupones.html", {"request": request, "cupones": cupones})

# Crear (GET)
@router.get("/admin/cupones/crear", dependencies=[Depends(current_superuser)])
def form_crear_cupon(request: Request):
    return templates.TemplateResponse("admin_cupon_form.html", {"request": request, "modo": "crear", "cupon": None})

# Crear (POST)
@router.post("/admin/cupones/crear", dependencies=[Depends(current_superuser)])
def crear_cupon(
    codigo: str = Form(...),
    descripcion: str = Form(None),
    tipo_descuento: str = Form(...),
    valor: float = Form(...),
    fecha_inicio: str = Form(...),
    fecha_fin: str = Form(...),
    activo: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    cupon = Cupon(
        codigo=codigo,
        descripcion=descripcion,
        tipo_descuento=tipo_descuento,
        valor=valor,
        fecha_inicio=datetime.fromisoformat(fecha_inicio),
        fecha_fin=datetime.fromisoformat(fecha_fin),
        activo=True if activo == "on" else False,
    )
    db.add(cupon)
    db.commit()
    return RedirectResponse("/admin/cupones", status_code=303)

# Editar (GET)
@router.get("/admin/cupones/{cupon_id}/editar", dependencies=[Depends(current_superuser)])
def form_editar_cupon(cupon_id: int, request: Request, db: Session = Depends(get_db)):
    cupon = db.query(Cupon).get(cupon_id)
    return templates.TemplateResponse("admin_cupon_form.html", {"request": request, "modo": "editar", "cupon": cupon})

# Editar (POST)
@router.post("/admin/cupones/{cupon_id}/editar", dependencies=[Depends(current_superuser)])
def editar_cupon(
    cupon_id: int,
    codigo: str = Form(...),
    descripcion: str = Form(None),
    tipo_descuento: str = Form(...),
    valor: float = Form(...),
    fecha_inicio: str = Form(...),
    fecha_fin: str = Form(...),
    activo: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    cupon = db.query(Cupon).get(cupon_id)
    if not cupon:
        return RedirectResponse("/admin/cupones", status_code=303)

    cupon.codigo = codigo
    cupon.descripcion = descripcion
    cupon.tipo_descuento = tipo_descuento
    cupon.valor = valor
    cupon.fecha_inicio = datetime.fromisoformat(fecha_inicio)
    cupon.fecha_fin = datetime.fromisoformat(fecha_fin)
    cupon.activo = True if activo == "on" else False

    db.commit()
    return RedirectResponse("/admin/cupones", status_code=303)

# Eliminar
@router.post("/admin/cupones/{cupon_id}/eliminar", dependencies=[Depends(current_superuser)])
def eliminar_cupon(cupon_id: int, db: Session = Depends(get_db)):
    cupon = db.query(Cupon).get(cupon_id)
    if cupon:
        # Eliminar todos los registros de usos asociados
        db.query(CuponUso).filter(CuponUso.cupon_id == cupon_id).delete(synchronize_session=False)
        # Eliminar el cupón
        db.delete(cupon)
        db.commit()
    return RedirectResponse("/admin/cupones", status_code=303)
