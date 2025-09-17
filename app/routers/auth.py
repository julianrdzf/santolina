from fastapi_users import FastAPIUsers
from fastapi import APIRouter, Request, Depends, status
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.models.user import Usuario
from app.dependencies.users import get_user_manager
from fastapi_users.authentication import CookieTransport, AuthenticationBackend, JWTStrategy
from httpx_oauth.clients.google import GoogleOAuth2
from fastapi.responses import RedirectResponse, Response
from app.user_manager import UserManager
import uuid
import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

SECRET = os.getenv("SECRET_AUTH")
GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_OAUTH_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")

# Google OAuth client
# Custom CookieTransport with automatic redirect after OAuth login
class AutoRedirectCookieTransport(CookieTransport):
    async def get_login_response(self, token: str) -> Response:
        response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
        return self._set_login_cookie(response, token)

google_oauth_client = GoogleOAuth2(
    GOOGLE_OAUTH_CLIENT_ID,
    GOOGLE_OAUTH_CLIENT_SECRET,
)

cookie_transport = AutoRedirectCookieTransport(cookie_name="auth", cookie_max_age=3600)

def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[Usuario, uuid.UUID](
    get_user_manager,
    [auth_backend],
)

current_active_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)
optional_current_user = fastapi_users.current_user(optional=True)

router = APIRouter()

# Rutas de autenticación JWT (login/logout)
router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

# Registro
router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

# Usuarios actuales / admin
router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)

# Google OAuth
router.include_router(
    fastapi_users.get_oauth_router(
        google_oauth_client,
        auth_backend,
        SECRET,
        associate_by_email=True,
        is_verified_by_default=True,
    ),
    prefix="/auth/google",
    tags=["auth"],
)

# The OAuth callback is now handled automatically by FastAPI Users
# with the custom AutoRedirectCookieTransport that redirects to "/"