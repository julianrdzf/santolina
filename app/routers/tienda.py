from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db import get_db
from app.models.categorias_productos import CategoriaProducto
from app.models.productos import Producto

router = APIRouter()
templates = Jinja2Templates(directory="frontend/templates")

@router.get("/tienda")
def tienda(
    request: Request,
    db: Session = Depends(get_db),
    page: int = 1,
    q: str = "",
    categoria: list[int] = None
):
    query = db.query(Producto)

    if q:
        query = query.filter(
            Producto.nombre.ilike(f"%{q}%") |
            Producto.descripcion.ilike(f"%{q}%")
        )
    if categoria:
        query = query.filter(Producto.id_categoria.in_(categoria))

    items_per_page = 12
    total = query.count()
    productos = query.offset((page-1)*items_per_page).limit(items_per_page).all()
    total_pages = (total + items_per_page - 1) // items_per_page

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        # Devolver solo el HTML del grid (partial)
        return templates.TemplateResponse(
            "partials/productos_grid.html",
            {"request": request, "productos": productos}
        )

    categorias = db.query(CategoriaProducto).all()

    return templates.TemplateResponse(
        "tienda.html",
        {
            "request": request,
            "productos": productos,
            "categorias": categorias,
            "page": page,
            "total_pages": total_pages,
            "q": q,
            "selected_cats": categoria or []
        }
    )