from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pathlib import Path
from fastapi.templating import Jinja2Templates
from app.routers import categorias, eventos, reservas, admin, admin_eventos, admin_ebooks, contacto, usuarios, mercado_pago, tienda, ebooks, paypal
from fastapi import FastAPI
from app.mail_utils import enviar_mail_prueba
from app.routers.auth import router as auth_router
from app.models.user import Usuario
import locale
import os

# Configura la localización a español
# Preferir variables de entorno si están definidas (útil en Railway)
os.environ.setdefault("LC_ALL", os.environ.get("LC_ALL", "C.UTF-8"))
os.environ.setdefault("LANG", os.environ.get("LANG", "C.UTF-8"))

def try_set_locales(preferred_locales):
    """
    Intentar setear la primera locale disponible de la lista preferred_locales.
    No lanza excepción si ninguna está disponible.
    """
    for loc in preferred_locales:
        try:
            locale.setlocale(locale.LC_TIME, loc)
            # si necesitás otras categorías, ponerlas aquí también:
            # locale.setlocale(locale.LC_MONETARY, loc)
            # locale.setlocale(locale.LC_NUMERIC, loc)
            print(f"Locale establecida: {loc}")
            return loc
        except locale.Error:
            # seguir intentando con la siguiente
            continue
    # Si no encontramos ninguna, intentamos la locale por defecto del sistema ("")
    try:
        locale.setlocale(locale.LC_TIME, "")
        print("Locale establecida por defecto del sistema")
        return ""
    except locale.Error:
        # ninguna disponible: se continúa sin setear (usar defaults)
        print("No se pudo establecer locale; usando valores por defecto (C).")
        return None

# Lista de preferencia: primero la que querés, luego alternativas
PREFERRED_LOCALES = ["es_ES.UTF-8", "es_ES", "C.UTF-8"]

try_set_locales(PREFERRED_LOCALES)



# Aplicación
app = FastAPI()

# Middleware para manejar proxy headers (Railway usa HTTPS)
@app.middleware("http")
async def add_proxy_headers(request: Request, call_next):
    # Railway pasa estos headers cuando está detrás de un proxy HTTPS
    if "x-forwarded-proto" in request.headers:
        request.scope["scheme"] = request.headers["x-forwarded-proto"]
    response = await call_next(request)
    return response

app.include_router(eventos.router)
app.include_router(categorias.router)
app.include_router(reservas.router)
app.include_router(admin.router)
app.include_router(admin_eventos.router)
app.include_router(admin_ebooks.router)
app.include_router(contacto.router)
app.include_router(auth_router)
app.include_router(usuarios.router)
app.include_router(mercado_pago.router)
app.include_router(tienda.router)
app.include_router(ebooks.router)
app.include_router(paypal.router)



BASE_DIR = Path(__file__).resolve().parent.parent
# Servir la carpeta frontend como estáticos
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "frontend" / "static")), name="static")

templates = Jinja2Templates(directory=str(BASE_DIR / "frontend" / "templates"))

@app.get("/health")
def health():
    return {"status": "ok"}

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

@app.get("/reiki-sesion", response_class=HTMLResponse)
async def mostrar_reiki_sesion(request: Request):
    return templates.TemplateResponse("reiki_sesion.html", {"request": request})

@app.get("/pendulo-hebreo", response_class=HTMLResponse)
async def mostrar_pendulo(request: Request):
    return templates.TemplateResponse("pendulo_hebreo.html", {"request": request})

@app.get("/terapia-floral", response_class=HTMLResponse)
async def mostrar_floral(request: Request):
    return templates.TemplateResponse("terapia_floral.html", {"request": request})

@app.get("/constelaciones", response_class=HTMLResponse)
async def mostrar_contelaciones(request: Request):
    return templates.TemplateResponse("constelaciones.html", {"request": request})

@app.get("/reiki-iniciacion", response_class=HTMLResponse)
async def mostrar_reiki_iniciacion(request: Request):
    return templates.TemplateResponse("reiki_iniciacion.html", {"request": request})

@app.get("/recetas", response_class=HTMLResponse)
async def mostrar_recetas(request: Request):
    return templates.TemplateResponse("recetas.html", {"request": request})

@app.get("/ritual-utero", response_class=HTMLResponse)
async def mostrar_ritual_utero(request: Request):
    return templates.TemplateResponse("ritual_utero.html", {"request": request})

@app.get("/limpieza-energetica", response_class=HTMLResponse)
async def mostrar_limpieza_energetica(request: Request):
    return templates.TemplateResponse("limpieza_energetica.html", {"request": request})



###########################
##Test


#@app.get("/test-email")
#async def test_email():
#    await enviar_mail_prueba("aqui_mail_test@test.com")
#    return {"mensaje": "Correo enviado correctamente"}