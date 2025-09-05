from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base

class ImagenProducto(Base):
    __tablename__ = "imagenes_producto"

    id = Column(Integer, primary_key=True, index=True)
    id_producto = Column(Integer, ForeignKey("productos.id"), nullable=False)
    url_imagen = Column(String, nullable=False)
    descripcion = Column(String, nullable=True)
    public_id = Column(String, nullable=False) 

    producto = relationship("Producto", back_populates="imagenes")