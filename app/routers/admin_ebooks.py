from fastapi import APIRouter, Request, Depends, UploadFile, File, HTTPException, Form, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session, joinedload
from app.db import get_db
from app.models.categorias_ebooks import CategoriaEbook
from app.models.ebooks import Ebook
from app.models.compra_ebooks import CompraEbook
from app.routers.auth import current_superuser
from typing import Optional
import math
import cloudinary.uploader

router = APIRouter()
templates = Jinja2Templates(directory="frontend/templates")

# Panel de ebooks
@router.get("/admin/ebooks-panel", dependencies=[Depends(current_superuser)])
def admin_ebooks_panel(request: Request):
    return templates.TemplateResponse("admin_ebooks_panel.html", {"request": request})

#############################
# Categorías de Ebooks

# Listar categorías de ebooks
@router.get("/admin/categorias_ebooks", dependencies=[Depends(current_superuser)])
def listar_categorias_ebooks(request: Request, db: Session = Depends(get_db)):
    categorias = db.query(CategoriaEbook).all()
    return templates.TemplateResponse("admin_categorias_ebooks.html", {
        "request": request,
        "categorias": categorias
    })

@router.get("/admin/categorias_ebooks/padres", dependencies=[Depends(current_superuser)])
def listar_categorias_ebooks_padres(request: Request, db: Session = Depends(get_db)):
    # Filtramos solo las categorías que no tienen padre
    categorias_padres = db.query(CategoriaEbook).filter(CategoriaEbook.id_categoria_padre == None).all()

    return templates.TemplateResponse("admin_categorias_ebooks.html", {
        "request": request,
        "categorias": categorias_padres,
        "titulo": "Categorías principales de ebooks"
    })

@router.get("/admin/categorias_ebooks/{categoria_id}/hijos", dependencies=[Depends(current_superuser)])
def listar_hijos_categoria_ebook(categoria_id: int, request: Request, db: Session = Depends(get_db)):
    # Buscamos la categoría padre
    categoria_padre = db.query(CategoriaEbook).get(categoria_id)
    if not categoria_padre:
        return templates.TemplateResponse("404.html", {"request": request})

    # Tomamos solo las subcategorías
    subcategorias = categoria_padre.subcategorias

    return templates.TemplateResponse("admin_categorias_ebooks.html", {
        "request": request,
        "categorias": subcategorias,
        "categoria_padre": categoria_padre
    })

# Mostrar formulario crear categoría ebook
@router.get("/admin/categorias_ebooks/crear", dependencies=[Depends(current_superuser)])
def mostrar_formulario_crear_categoria_ebook(request: Request, db: Session = Depends(get_db)):
    categorias = db.query(CategoriaEbook).all()  # para seleccionar padre opcional
    return templates.TemplateResponse("admin_categoria_ebook_form.html", {
        "request": request,
        "categorias": categorias,
        "modo": "crear"
    })

# Crear categoría ebook
@router.post("/admin/categorias_ebooks/crear", dependencies=[Depends(current_superuser)])
def crear_categoria_ebook(
    nombre: str = Form(...), 
    id_categoria_padre: Optional[str] = Form(None), 
    db: Session = Depends(get_db)
):
    # Si vino vacío, lo convierto a None
    id_categoria_padre = int(id_categoria_padre) if id_categoria_padre else None

    if id_categoria_padre is not None:
        padre = db.query(CategoriaEbook).get(id_categoria_padre)
        if not padre:
            return templates.TemplateResponse("error_admin.html", {
                "request": {},
                "mensaje": "La categoría padre seleccionada no existe.",
                "url_volver": "/admin/categorias_ebooks"
            })
    
    nueva_categoria = CategoriaEbook(
        nombre=nombre,
        id_categoria_padre=id_categoria_padre
    )
    db.add(nueva_categoria)
    db.commit()
    return RedirectResponse(url="/admin/categorias_ebooks", status_code=303)

# Mostrar formulario editar categoría ebook
@router.get("/admin/categorias_ebooks/{categoria_id}/editar", dependencies=[Depends(current_superuser)])
def mostrar_formulario_editar_categoria_ebook(categoria_id: int, request: Request, db: Session = Depends(get_db)):
    categoria = db.query(CategoriaEbook).get(categoria_id)
    if not categoria:
        return templates.TemplateResponse("404.html", {"request": request})
    categorias = db.query(CategoriaEbook).filter(CategoriaEbook.id != categoria_id).all()
    return templates.TemplateResponse("admin_categoria_ebook_form.html", {
        "request": request,
        "categoria": categoria,
        "categorias": categorias,
        "modo": "editar"
    })

# Actualizar categoría ebook
@router.post("/admin/categorias_ebooks/{categoria_id}/editar", dependencies=[Depends(current_superuser)])
def actualizar_categoria_ebook(
    categoria_id: int, 
    nombre: str = Form(...), 
    id_categoria_padre: Optional[str] = Form(None), 
    db: Session = Depends(get_db)
):
    # Si vino vacío, lo convierto a None
    id_categoria_padre = int(id_categoria_padre) if id_categoria_padre else None

    categoria = db.query(CategoriaEbook).get(categoria_id)
    if not categoria:
        return RedirectResponse(url="/admin/categorias_ebooks", status_code=303)

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
                "url_volver": "/admin/categorias_ebooks"
            })
        ancestro = db.query(CategoriaEbook).get(ancestro_id)
        ancestro_id = ancestro.id_categoria_padre if ancestro else None

    categoria.nombre = nombre
    categoria.id_categoria_padre = id_categoria_padre
    db.commit()
    return RedirectResponse(url="/admin/categorias_ebooks", status_code=303)

@router.post("/admin/categorias_ebooks/{categoria_id}/eliminar", dependencies=[Depends(current_superuser)])
def eliminar_categoria_ebook(categoria_id: int, db: Session = Depends(get_db)):
    categoria = db.query(CategoriaEbook).get(categoria_id)
    if categoria:
        # Verificar si tiene subcategorías
        hijos = db.query(CategoriaEbook).filter(CategoriaEbook.id_categoria_padre == categoria_id).all()
        if hijos:
            return templates.TemplateResponse("error_admin.html", {
                "request": {},
                "mensaje": "No se puede eliminar la categoría porque tiene subcategorías asociadas.",
                "url_volver": "/admin/categorias_ebooks"
            })

        # Verificar si tiene ebooks asociados
        ebooks = db.query(Ebook).filter(Ebook.id_categoria == categoria_id).all()
        if ebooks:
            return templates.TemplateResponse("error_admin.html", {
                "request": {},
                "mensaje": "No se puede eliminar la categoría porque tiene ebooks asociados.",
                "url_volver": "/admin/categorias_ebooks"
            })

        db.delete(categoria)
        db.commit()
    return RedirectResponse(url="/admin/categorias_ebooks", status_code=303)

###########################
# Ebooks

@router.get("/admin/ebooks", dependencies=[Depends(current_superuser)])
def listar_ebooks(request: Request, db: Session = Depends(get_db)):
    ebooks = db.query(Ebook).all()
    return templates.TemplateResponse("admin_ebooks.html", {
        "request": request,
        "ebooks": ebooks
    })

@router.get("/admin/ebooks/crear", dependencies=[Depends(current_superuser)])
def mostrar_formulario_crear_ebook(request: Request, db: Session = Depends(get_db)):
    categorias = db.query(CategoriaEbook).all()
    return templates.TemplateResponse("admin_ebook_form.html", {
        "request": request,
        "categorias": categorias,
        "modo": "crear"
    })

@router.post("/admin/ebooks/crear")
async def crear_ebook(
    request: Request,
    titulo: str = Form(...),
    descripcion: str = Form(""),
    precio: float = Form(...),
    id_categoria: Optional[int] = Form(None),
    url_archivo: UploadFile = File(...),
    imagen_portada: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    try:
        # Subir archivo PDF a Cloudinary
        pdf_result = cloudinary.uploader.upload(
            url_archivo.file,
            resource_type="raw",
            folder="ebooks/archivos",
            public_id=f"ebook_{titulo.replace(' ', '_')}.pdf"
        )
        
        # Subir imagen de portada si se proporciona
        imagen_url = None
        if imagen_portada and imagen_portada.filename:
            imagen_result = cloudinary.uploader.upload(
                imagen_portada.file,
                folder="ebooks/portadas",
                transformation=[
                    {"width": 400, "height": 600, "crop": "fill"},
                    {"quality": "auto"},
                    {"fetch_format": "auto"}
                ]
            )
            imagen_url = imagen_result["secure_url"]
        
        # Crear el ebook en la base de datos
        nuevo_ebook = Ebook(
            titulo=titulo,
            descripcion=descripcion,
            precio=precio,
            id_categoria=id_categoria,
            url_archivo=pdf_result["secure_url"],
            imagen_portada=imagen_url,
            activo=True
        )
        
        db.add(nuevo_ebook)
        db.commit()
        
        return RedirectResponse(url="/admin/ebooks", status_code=303)
        
    except Exception as e:
        return templates.TemplateResponse("error_admin.html", {
            "request": request,
            "mensaje": f"Error al crear el ebook: {str(e)}",
            "url_volver": "/admin/ebooks"
        })

@router.get("/admin/ebooks/{ebook_id}/editar", dependencies=[Depends(current_superuser)])
def mostrar_formulario_editar_ebook(ebook_id: int, request: Request, db: Session = Depends(get_db)):
    ebook = db.query(Ebook).get(ebook_id)
    categorias = db.query(CategoriaEbook).all()
    if not ebook:
        return templates.TemplateResponse("404.html", {"request": request})
    return templates.TemplateResponse("admin_ebook_form.html", {
        "request": request,
        "ebook": ebook,
        "categorias": categorias,
        "modo": "editar"
    })

@router.post("/admin/ebooks/{ebook_id}/editar")
async def actualizar_ebook(
    ebook_id: int,
    request: Request,
    titulo: str = Form(...),
    descripcion: str = Form(""),
    precio: float = Form(...),
    id_categoria: Optional[int] = Form(None),
    url_archivo: UploadFile = File(None),
    imagen_portada: UploadFile = File(None),
    activo: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    ebook = db.query(Ebook).get(ebook_id)
    if not ebook:
        return RedirectResponse(url="/admin/ebooks", status_code=303)
    
    try:
        # Actualizar datos básicos
        ebook.titulo = titulo
        ebook.descripcion = descripcion
        ebook.precio = precio
        ebook.id_categoria = id_categoria
        ebook.activo = True if activo == "on" else False
        
        # Actualizar archivo PDF si se proporciona uno nuevo
        if url_archivo and url_archivo.filename:
            # Eliminar archivo anterior de Cloudinary si existe
            if ebook.url_archivo:
                try:
                    # Extraer public_id del URL anterior
                    old_public_id = f"ebook_{ebook.titulo.replace(' ', '_')}.pdf"
                    cloudinary.uploader.destroy(old_public_id, resource_type="raw")
                except Exception as e:
                    print(f"Error eliminando archivo anterior: {e}")
            
            pdf_result = cloudinary.uploader.upload(
                url_archivo.file,
                resource_type="raw",
                folder="ebooks/archivos",
                public_id=f"ebook_{titulo.replace(' ', '_')}.pdf"
            )
            ebook.url_archivo = pdf_result["secure_url"]
        
        # Actualizar imagen de portada si se proporciona una nueva
        if imagen_portada and imagen_portada.filename:
            # Eliminar imagen anterior de Cloudinary si existe
            if ebook.imagen_portada:
                try:
                    # Extraer public_id del URL anterior
                    old_public_id = f"ebooks/portadas/ebook_{ebook.titulo.replace(' ', '_')}"
                    cloudinary.uploader.destroy(old_public_id)
                except Exception as e:
                    print(f"Error eliminando imagen anterior: {e}")
            
            imagen_result = cloudinary.uploader.upload(
                imagen_portada.file,
                folder="ebooks/portadas",
                public_id=f"ebook_{titulo.replace(' ', '_')}",
                transformation=[
                    {"width": 400, "height": 600, "crop": "fill"},
                    {"quality": "auto"},
                    {"fetch_format": "auto"}
                ]
            )
            ebook.imagen_portada = imagen_result["secure_url"]
        
        db.commit()
        return RedirectResponse(url="/admin/ebooks", status_code=303)
        
    except Exception as e:
        return templates.TemplateResponse("error_admin.html", {
            "request": request,
            "mensaje": f"Error al actualizar el ebook: {str(e)}",
            "url_volver": "/admin/ebooks"
        })

@router.post("/admin/ebooks/{ebook_id}/eliminar", dependencies=[Depends(current_superuser)])
def eliminar_ebook(ebook_id: int, db: Session = Depends(get_db)):
    ebook = db.query(Ebook).get(ebook_id)
    if ebook:
        # Verificar si tiene compras asociadas
        compras = db.query(CompraEbook).filter(CompraEbook.ebook_id == ebook_id).all()
        if compras:
            return templates.TemplateResponse("error_admin.html", {
                "request": {},
                "mensaje": "No se puede eliminar el ebook porque tiene compras asociadas.",
                "url_volver": "/admin/ebooks"
            })
        
        db.delete(ebook)
        db.commit()
    return RedirectResponse(url="/admin/ebooks", status_code=303)

###########################
# Compras de Ebooks

@router.get("/admin/compras_ebooks", dependencies=[Depends(current_superuser)])
def listar_compras_ebooks_admin(
    request: Request,
    page: int = Query(1, ge=1),
    estado: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Página de administración para ver todas las compras de ebooks"""
    
    # Configuración de paginación
    items_per_page = 20
    offset = (page - 1) * items_per_page
    
    # Query base para compras de ebooks
    query = db.query(CompraEbook).options(
        joinedload(CompraEbook.usuario),
        joinedload(CompraEbook.ebook)
    )
    
    # Filtro por estado de pago
    if estado and estado in ['pendiente', 'pagado', 'fallido', 'cancelado']:
        query = query.filter(CompraEbook.estado_pago == estado)
    
    # Contar total de resultados para paginación
    total_compras = query.count()
    total_pages = math.ceil(total_compras / items_per_page)
    
    # Obtener compras de la página actual
    compras = query.order_by(CompraEbook.fecha_compra.desc()).offset(offset).limit(items_per_page).all()
    
    # Calcular estadísticas
    stats = {
        'total': db.query(CompraEbook).count(),
        'pagadas': db.query(CompraEbook).filter(CompraEbook.estado_pago == 'pagado').count(),
        'pendientes': db.query(CompraEbook).filter(CompraEbook.estado_pago == 'pendiente').count(),
        'fallidas': db.query(CompraEbook).filter(CompraEbook.estado_pago == 'fallido').count()
    }
    
    return templates.TemplateResponse("admin_compra_ebooks.html", {
        "request": request,
        "compras": compras,
        "stats": stats,
        "estado_filtro": estado,
        "page": page,
        "total_pages": total_pages,
        "total_compras": total_compras
    })
