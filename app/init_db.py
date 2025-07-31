from app.db import engine, Base
from app.models.user import Usuario
from app.models.evento import Evento
from app.models.reserva import Reserva
from app.models.categorias import Categoria


def init_db():
    """Initialize the database by creating all tables"""
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
        init_db() 