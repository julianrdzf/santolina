from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from fastapi import Form, status
from fastapi.responses import RedirectResponse
from app.dependencies.users import get_user_manager
from fastapi import Depends
from app.models.user import Usuario
from app.schemas.user import UserCreate



from fastapi_users.authentication import JWTStrategy
from fastapi_users.router.common import ErrorCode
from fastapi_users import exceptions
from app.routers.auth import auth_backend, fastapi_users, cookie_transport

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
        response.headers["Location"] = "/"  # Redirigir al home
        response.status_code = 302

        return response

    except Exception as e:
        return HTMLResponse(content=f"<h3>Error: {e}</h3>", status_code=400)

@router.get("/login")
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

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