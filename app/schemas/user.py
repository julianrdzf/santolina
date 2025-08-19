from typing import Optional
from uuid import UUID
from fastapi_users import schemas
from pydantic import EmailStr

class UserRead(schemas.BaseUser[UUID]):
    nombre: str
    celular: Optional[str] = None

class UserCreate(schemas.BaseUserCreate):
    nombre: str
    celular: Optional[str] = None
    password: Optional[str] = None

class UserUpdate(schemas.BaseUserUpdate):
    nombre: Optional[str] = None
    celular: Optional[str] = None