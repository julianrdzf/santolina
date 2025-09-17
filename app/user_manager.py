from fastapi import Request
from fastapi_users import BaseUserManager, UUIDIDMixin
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from app.models.user import Usuario
from app.models.oauth_account import OAuthAccount
from app.schemas.user import UserCreate
import uuid
import os
from dotenv import load_dotenv
from pathlib import Path
from app.mail_utils import enviar_mail_password_reset
from typing import Optional, Dict, Any


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

    async def create(
        self,
        user_create: UserCreate,
        safe: bool = False,
        request: Optional[Request] = None,
    ) -> Usuario:
        # Set default name from email if not provided
        if not user_create.nombre:
            # Extract name from email (part before @)
            email_name = user_create.email.split('@')[0]
            user_create.nombre = email_name
        
        return await super().create(user_create, safe, request)

    async def oauth_callback(
        self,
        oauth_name: str,
        access_token: str,
        account_id: str,
        account_email: str,
        expires_at: Optional[int] = None,
        refresh_token: Optional[str] = None,
        request: Optional[Request] = None,
        *,
        associate_by_email: bool = False,
        is_verified_by_default: bool = False,
    ) -> Usuario:
        # Try to get existing OAuth account
        try:
            # Query OAuth account directly from database
            from sqlalchemy import select
            stmt = select(OAuthAccount).where(
                OAuthAccount.oauth_name == oauth_name,
                OAuthAccount.account_id == account_id
            )
            result = await self.user_db.session.execute(stmt)
            oauth_account = result.scalar_one_or_none()
            
            if oauth_account:
                user = await self.get(oauth_account.user_id)
            else:
                user = None
        except:
            oauth_account = None
            user = None

        # If no OAuth account found, try to associate by email if enabled
        if not user and associate_by_email:
            try:
                user = await self.get_by_email(account_email)
            except:
                user = None

        # If still no user, create a new one
        if not user:
            # Get user name from Google profile
            try:
                import httpx
                async with httpx.AsyncClient() as client:
                    profile_response = await client.get(
                        "https://www.googleapis.com/oauth2/v2/userinfo",
                        headers={"Authorization": f"Bearer {access_token}"}
                    )
                    if profile_response.status_code == 200:
                        profile_data = profile_response.json()
                        google_name = profile_data.get("name", account_email.split('@')[0])
                    else:
                        google_name = account_email.split('@')[0]
            except:
                google_name = account_email.split('@')[0]

            # Create user data for OAuth registration
            # Generate a random password for OAuth users (they won't use it for login)
            import secrets
            fake_password = secrets.token_urlsafe(32)
            
            user_create_dict = {
                "email": account_email,
                "is_verified": is_verified_by_default,
                "nombre": google_name,  # Use name from Google profile
                "password": fake_password  # Random password for OAuth users
            }
            user_create = UserCreate(**user_create_dict)
            user = await self.create(user_create, safe=True, request=request)

        # Create or update OAuth account
        if not oauth_account:
            # Create new OAuth account directly using SQLAlchemy
            oauth_data = OAuthAccount(
                user_id=user.id,
                oauth_name=oauth_name,
                access_token=access_token,
                account_id=account_id,
                account_email=account_email,
                expires_at=expires_at,
                refresh_token=refresh_token,
            )
            self.user_db.session.add(oauth_data)
            await self.user_db.session.commit()
        else:
            # Update existing OAuth account
            oauth_account.access_token = access_token
            oauth_account.expires_at = expires_at
            oauth_account.refresh_token = refresh_token
            await self.user_db.session.commit()

        return user