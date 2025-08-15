from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.templating import Jinja2Templates
from app.routers import categorias, eventos, reservas, admin, contacto, usuarios, mercado_pago
from fastapi import FastAPI
from app.mail_utils import enviar_mail_prueba
from app.routers.auth import router as auth_router
from app.models.user import Usuario
import locale

# Configura la localización a español
locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')


app = FastAPI()
app.include_router(eventos.router)
app.include_router(categorias.router)
app.include_router(reservas.router)
app.include_router(admin.router)
app.include_router(contacto.router)
app.include_router(auth_router)
app.include_router(usuarios.router)
app.include_router(mercado_pago.router)



BASE_DIR = Path(__file__).resolve().parent.parent
# Servir la carpeta frontend como estáticos
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "frontend" / "static")), name="static")

templates = Jinja2Templates(directory=str(BASE_DIR / "frontend" / "templates"))

@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/reservas", response_class=HTMLResponse)
async def mostrar_formulario(request: Request):
    return templates.TemplateResponse("reservas.html", {"request": request})

@app.get("/yoga", response_class=HTMLResponse)
async def mostrar_yoga(request: Request):
    return templates.TemplateResponse("yoga.html", {"request": request})

@app.get("/yoga-gong", response_class=HTMLResponse)
async def mostrar_yoga_gong(request: Request):
    return templates.TemplateResponse("yoga_gong.html", {"request": request})

@app.get("/alimentacion", response_class=HTMLResponse)
async def mostrar_alimentacion(request: Request):
    return templates.TemplateResponse("alimentacion.html", {"request": request})




###########################
##Test


#@app.get("/test-email")
#async def test_email():
#    await enviar_mail_prueba("aqui_mail_test@test.com")
#    return {"mensaje": "Correo enviado correctamente"}