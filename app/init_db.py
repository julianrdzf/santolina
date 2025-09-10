
#from app.db import engine, Base
#from app.models.user import Usuario
#from app.models.evento import Evento
#from app.models.reserva import Reserva
#from app.models.categorias import Categoria


#def init_db():
#    """Initialize the database by creating all tables"""
#    Base.metadata.create_all(bind=engine)
#    print("Database tables created successfully!")

#if __name__ == "__main__":
#        init_db() 

# app/init_db.py
import os
import time
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Cargar .env (funciona tanto local como en Railway si no existe .env usa env vars)
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

from app.db import SessionLocal, Base, engine  # tu Base declarative
# Importá TODOS tus modelos aquí para que queden registrados en Base.metadata
# (ajustá nombres/paths si tus modelos están en otro lugar)
from app.models.user import Usuario
from app.models.evento import Evento
from app.models.reserva import Reserva
from app.models.categorias_eventos import CategoriaEvento

# Categorías y productos
from app.models.categorias_productos import CategoriaProducto
from app.models.productos import Producto
from app.models.imagenes_productos import ImagenProducto

# Promociones
from app.models.promociones import Promocion
from app.models.promocion_productos import PromocionProducto

# Carrito y detalle
from app.models.carritos import Carrito
from app.models.carrito_detalle import CarritoDetalle

# Órdenes y detalle
from app.models.ordenes import Orden
from app.models.orden_detalle import OrdenDetalle

# Pagos
from app.models.pagos import Pago

# Direcciones
from app.models.direcciones import Direccion

# Cupones y uso de cupones
from app.models.cupones import Cupon
from app.models.cupones_uso import CuponUso

# Envíos
from app.models.costos_envio import CostoEnvio

# Ebooks
from app.models.categorias_ebooks import CategoriaEbook
from app.models.ebooks import Ebook
from app.models.compra_ebooks import CompraEbook


from sqlalchemy import insert
from sqlalchemy.dialects.postgresql import insert as pg_insert

DATABASE_URL = os.getenv("DATABASE_URL", "")
# Parámetros de retry
MAX_RETRIES = int(os.getenv("INIT_DB_MAX_RETRIES", 10))
RETRY_DELAY = float(os.getenv("INIT_DB_RETRY_DELAY", 3.0))  # segundos (aumenta exponencialmente)

def ensure_sslmode(url: str) -> str:
    """
    Agrega sslmode=require si no viene y es PostgreSQL **y no estamos en localhost**.
    Para entornos locales (localhost/127.0.0.1) no fuerza SSL.
    """
    if not url:
        return url

    # Extraer host para distinguir local vs remoto
    # Esto asume URL típica: postgresql://usuario:pass@host:port/db
    from urllib.parse import urlparse
    parsed = urlparse(url)
    host = parsed.hostname

    # Si no es localhost, forzar sslmode=require
    if "postgresql" in url and "sslmode=" not in url and host not in ("localhost", "127.0.0.1"):
        sep = "&" if "?" in url else "?"
        return f"{url}{sep}sslmode=require"

    # Local o ya tiene sslmode
    return url

# Determinar si tenemos una URL async explícita o si hay que convertir
ASYNC_DATABASE_URL = None
if DATABASE_URL:
    if DATABASE_URL.startswith("postgresql+asyncpg://"):
        ASYNC_DATABASE_URL = ensure_sslmode(DATABASE_URL)
    elif DATABASE_URL.startswith("postgresql://"):
        # conversión automática: si la app se desplegó con URL sync, permitimos init async si queremos
        ASYNC_DATABASE_URL = ensure_sslmode(DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1))

# Permitir forzar el uso del init sync aun cuando haya +asyncpg
FORCE_SYNC_INIT = os.getenv("INIT_USE_SYNC", "false").lower() in ("1", "true", "yes")

# ----------------- Async init -----------------
async def init_db_async(async_url: str) -> None:
    from sqlalchemy.ext.asyncio import create_async_engine
    engine = create_async_engine(async_url, future=True)
    # Retry loop: intentamos conectar repetidamente hasta MAX_RETRIES
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with engine.begin() as conn:
                # Ejecuta create_all en el hilo sync sobre la conexión async
                await conn.run_sync(Base.metadata.create_all)
            print("✅ (async) Database tables created successfully!")
            await engine.dispose()
            return
        except Exception as e:
            print(f"⚠️  (async) Attempt {attempt}/{MAX_RETRIES} failed: {e}")
            if attempt == MAX_RETRIES:
                raise
            await asyncio.sleep(RETRY_DELAY * attempt)  # backoff
    await engine.dispose()

# ----------------- Sync init -----------------
def init_db_sync(sync_url: str) -> None:
    from sqlalchemy import create_engine
    engine = create_engine(sync_url, future=True)
    # Retry loop
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            Base.metadata.create_all(bind=engine)
            print("✅ (sync) Database tables created successfully!")
            #engine.dispose()
            return engine
        except Exception as e:
            print(f"⚠️  (sync) Attempt {attempt}/{MAX_RETRIES} failed: {e}")
            if attempt == MAX_RETRIES:
                raise
            time.sleep(RETRY_DELAY * attempt)  # backoff
    engine.dispose()

# ----------------- Entrypoint -----------------
def main():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL no está definida. Seteala en .env o en las env vars de Railway.")
    # normalize
    sync_url = ensure_sslmode(DATABASE_URL)
    # Si el usuario forzó sync, hacemos sync
    if FORCE_SYNC_INIT:
        print("→ Forzando inicialización en modo SYNC (INIT_USE_SYNC=true)")
        init_db_sync(sync_url)
        return

    # Preferimos try async init si tenemos ASYNC_DATABASE_URL
    if ASYNC_DATABASE_URL:
        print("→ Intentando inicialización ASYNC (usando asyncpg).")
        try:
            asyncio.run(init_db_async(ASYNC_DATABASE_URL))
            #return
        except Exception as e:
            print(f"❗ Falló init async: {e}")
            print("→ Intentando inicialización SYNC como fallback.")
            # caer al sync fallback
    else:
        print("→ No se detectó URL async; inicializando en modo SYNC.")

    # Fallback / sync init
    engine = init_db_sync(sync_url)

    print("✅ Base de datos inicializada. Las categorías de eventos se gestionan desde el panel de administración.")


if __name__ == "__main__":
    main()
