import asyncio
from app.user_manager import UserManager
from app.schemas.user import UserCreate
from app.dependencies.users import get_user_db

async def test_create_user():
    # Obtener el user_db asíncrono
    user_db_gen = get_user_db()
    user_db = await user_db_gen.__anext__()
    user_manager = UserManager(user_db)

    user_data = UserCreate(
        email="prueba@example.com",
        password="testpassword123",
        nombre="Usuario Prueba",
        celular="099123456"
    )
    try:
        user = await user_manager.create(user_data)
        print("Usuario creado:", user)
    except Exception as e:
        print("Error al crear usuario:", e)

if __name__ == "__main__":
    asyncio.run(test_create_user()) 