from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base
from datetime import datetime, timezone

class Ebook(Base):
    __tablename__ = "ebooks"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, nullable=False, index=True)
    descripcion = Column(Text, nullable=True)
    precio = Column(Float, nullable=False)
    imagen_portada = Column(String, nullable=True)  # URL de la imagen de portada
    imagen_public_id = Column(String, nullable=True)  # public_id de la imagen de portada
    url_archivo = Column(String, nullable=False)    # URL del archivo PDF
    archivo_public_id = Column(String, nullable=False)    # public id del archivo PDF
    id_categoria = Column(Integer, ForeignKey("categorias_ebooks.id"), nullable=True)
    fecha_publicacion = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    activo = Column(Boolean, default=True)          # Para activar/desactivar la venta
    
    # Relaciones
    categoria = relationship("CategoriaEbook", back_populates="ebooks")
    compras = relationship("CompraEbook", back_populates="ebook")
