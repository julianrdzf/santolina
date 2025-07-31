from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import AsyncSessionLocal
from app.models.user import Usuario
from app.user_manager import UserManager
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy.orm import sessionmaker
import uuid

async def get_user_db():
    async with AsyncSessionLocal() as session:
        yield SQLAlchemyUserDatabase(session, Usuario)

async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)