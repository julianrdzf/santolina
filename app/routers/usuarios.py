from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from fastapi import Form, status
from fastapi.responses import RedirectResponse
from app.dependencies.users import get_user_manager
from app.db import get_db
from app.models.user import Usuario
from app.models.reserva import Reserva
from app.models.ordenes import Orden
from app.models.orden_detalle import OrdenDetalle
from app.models.direcciones import Direccion
from app.models.compra_ebooks import CompraEbook
from app.models.horario_fecha_evento import HorarioFechaEvento
from app.models.fecha_evento import FechaEvento
from app.schemas.user import UserCreate
from app.dependencies.users import get_user_manager
from app.routers.auth import auth_backend, fastapi_users, cookie_transport, current_active_user
from fastapi_users.authentication import JWTStrategy
from fastapi_users.router.common import ErrorCode
from fastapi_users import exceptions
from fastapi_users.exceptions import UserNotExists

templates = Jinja2Templates(directory="frontend/templates")
router = APIRouter()

@router.get("/registro", response_class=HTMLResponse)
async def mostrar_registro(request: Request):
    return templates.TemplateResponse("registro.html", {"request": request})

@router.post("/registro")
async def registrar_usuario(
    request: Request,
    nombre: str = Form(...),
    email: str = Form(...),
    celular: str = Form(None),
    password: str = Form(...),
    confirm_password: str = Form(...),
    user_manager=Depends(get_user_manager)
):
    if password != confirm_password:
        return HTMLResponse(content="<h3>Las contraseñas no coinciden.</h3>", status_code=400)
    
    try:
        # Crear el usuario
        user_create = UserCreate(
            email=email,
            password=password,
            nombre=nombre,
            celular=celular
        )
        user = await user_manager.create(user_create)

        # Generar el token
        token = await auth_backend.get_strategy().write_token(user)

        # Crear respuesta con cookie (solo se pasa el token)
        response = await cookie_transport.get_login_response(token)
        # Redirigir según el parámetro redirect o al home por defecto
        form_data = await request.form()
        redirect_url = form_data.get("redirect")
        if not redirect_url or redirect_url == "None":
            redirect_url = "/"
        response.headers["Location"] = redirect_url
        response.status_code = 302

        return response

    except Exception as e:
        return HTMLResponse(content=f"<h3>Error: {e}</h3>", status_code=400)


@router.get("/login")
async def login_form(request: Request, redirect: str = None):
    return templates.TemplateResponse("login.html", {
        "request": request,
        "redirect": redirect
    })

@router.get("/forgot-password")
async def forgot_password_form(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request})

@router.post("/forgot-password")
async def forgot_password_submit(
    request: Request,
    email: str = Form(...),
    user_manager = Depends(get_user_manager),
):
    try:
        user = await user_manager.get_by_email(email)  # <- obtiene el usuario
    except UserNotExists:
        # Opcional: no revelar si el email existe
        # devuelve siempre la misma respuesta
        return templates.TemplateResponse(
            "forgot_password_enviado.html", {"request": request, "email": email}
        )

    # Genera el token y dispara on_after_forgot_password
    await user_manager.forgot_password(user, request=request)

    return templates.TemplateResponse(
        "forgot_password_enviado.html", {"request": request, "email": email}
    )

@router.get("/reset-password")
async def reset_password_form(request: Request, token: str):
    return templates.TemplateResponse("reset_password.html", {"request": request, "token": token})

@router.post("/reset-password")
async def reset_password_submit(
    request: Request,
    token: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    user_manager = Depends(get_user_manager)
):
    if password != confirm_password:
        return HTMLResponse("<h3>Las contraseñas no coinciden</h3>", status_code=400)
    await user_manager.reset_password(token, password, request)
    # Podés loguearlo automáticamente o redirigir al login
    return RedirectResponse(url="/login", status_code=303)


@router.get("/perfil")
def perfil_usuario(
    request: Request,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(current_active_user)
):
    # Obtener órdenes del usuario con relaciones
    ordenes = db.query(Orden).options(
        joinedload(Orden.direccion_envio),
        joinedload(Orden.metodo_envio),
        joinedload(Orden.detalle).joinedload(OrdenDetalle.producto)
    ).filter(Orden.usuario_id == usuario.id).order_by(Orden.fecha.desc()).all()
    
    # Obtener reservas del usuario con relaciones necesarias
    reservas = db.query(Reserva).options(
        joinedload(Reserva.horario).joinedload(HorarioFechaEvento.fecha_evento).joinedload(FechaEvento.evento)
    ).filter(Reserva.usuario_id == usuario.id).order_by(Reserva.fecha_creacion.desc()).all()
    
    # Obtener direcciones del usuario
    direcciones = db.query(Direccion).filter(Direccion.usuario_id == usuario.id).all()
    
    # Obtener ebooks comprados del usuario
    compras_ebooks = db.query(CompraEbook).filter(
        CompraEbook.usuario_id == usuario.id,
        CompraEbook.estado_pago == "pagado"
    ).order_by(CompraEbook.fecha_compra.desc()).all()
    
    return templates.TemplateResponse("perfil.html", {
        "request": request,
        "usuario": usuario,
        "ordenes": ordenes,
        "reservas": reservas,
        "direcciones": direcciones,
        "compras_ebooks": compras_ebooks
    })


@router.post("/perfil/actualizar-datos")
def actualizar_datos_usuario(
    request: Request,
    nombre: str = Form(...),
    celular: str = Form(None),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(current_active_user)
):
    usuario.nombre = nombre
    usuario.celular = celular
    db.commit()
    
    return RedirectResponse(url="/perfil", status_code=303)


@router.post("/perfil/agregar-direccion")
def agregar_direccion_perfil(
    request: Request,
    direccion: str = Form(...),
    detalle: str = Form(None),
    ciudad: str = Form(...),
    departamento: str = Form(...),
    codigo_postal: str = Form(None),
    tipo: str = Form(None),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(current_active_user)
):
    nueva_direccion = Direccion(
        usuario_id=usuario.id,
        direccion=direccion,
        detalle=detalle,
        ciudad=ciudad,
        departamento=departamento,
        codigo_postal=codigo_postal if codigo_postal else None,
        pais="Uruguay",
        tipo=tipo
    )
    
    db.add(nueva_direccion)
    db.commit()
    
    return RedirectResponse(url="/perfil", status_code=303)


@router.post("/perfil/eliminar-direccion/{direccion_id}")
def eliminar_direccion(
    direccion_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(current_active_user)
):
    direccion = db.query(Direccion).filter(
        Direccion.id == direccion_id,
        Direccion.usuario_id == usuario.id
    ).first()
    
    if direccion:
        db.delete(direccion)
        db.commit()
    
    return RedirectResponse(url="/perfil", status_code=303)