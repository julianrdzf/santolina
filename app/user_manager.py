from fastapi import Request
from fastapi_users import BaseUserManager, UUIDIDMixin
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from app.models.user import Usuario
import uuid
import os
from dotenv import load_dotenv
from pathlib import Path
from app.mail_utils import enviar_mail_password_reset
from typing import Optional


env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
load_dotenv()
SECRET = os.getenv("SECRET_AUTH")  

class UserManager(UUIDIDMixin, BaseUserManager[Usuario, uuid.UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: Usuario, request=None):
        print(f"Usuario registrado: {user.email}")

    async def on_after_forgot_password(self, user: Usuario, token: str, request: Optional[Request] = None):
        # Link al frontend que mostrará el form pidiendo nueva contraseña
        base_url = os.getenv("BASE_URL", "http://localhost:8000")
        reset_link = f"{base_url}/reset-password?token={token}"
        await enviar_mail_password_reset(destinatario=user.email, reset_link=reset_link)

    async def on_after_reset_password(self, user: Usuario, request: Optional[Request] = None):
        # opcional: avisar al usuario o al admin
        pass