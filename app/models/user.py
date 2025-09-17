from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.db import Base

class Usuario(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "usuarios"
    nombre = Column(String, nullable=True)  # Opcional para usuarios OAuth
    celular = Column(String, nullable=True)

    reservas = relationship("Reserva", back_populates="usuario", cascade="all, delete-orphan")
    carritos = relationship("Carrito", back_populates="usuario", cascade="all, delete-orphan")
    direcciones = relationship("Direccion", back_populates="usuario", cascade="all, delete-orphan")
    ordenes = relationship("Orden", back_populates="usuario", cascade="all, delete-orphan")
    compras_ebooks = relationship("CompraEbook", back_populates="usuario", cascade="all, delete-orphan")