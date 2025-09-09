from fastapi import APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models.categorias_ebooks import CategoriaEbook
from app.routers.auth import current_superuser
from typing import Optional

router = APIRouter()
templates = Jinja2Templates(directory="frontend/templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

###########################
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
        "titulo": "Categorías principales de Ebooks"
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

        # Verificar si tiene ebooks asociados (cuando implementemos el modelo Ebook)
        # ebooks = db.query(Ebook).filter(Ebook.id_categoria == categoria_id).all()
        # if ebooks:
        #     return templates.TemplateResponse("error_admin.html", {
        #         "request": {},
        #         "mensaje": "No se puede eliminar la categoría porque tiene ebooks asociados.",
        #         "url_volver": "/admin/categorias_ebooks"
        #     })

        db.delete(categoria)
        db.commit()
    return RedirectResponse(url="/admin/categorias_ebooks", status_code=303)
