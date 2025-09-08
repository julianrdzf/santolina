import sys
import os
from datetime import datetime, timedelta

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import SessionLocal, Base, engine
from app.models.cupones import Cupon
from app.models.cupones_uso import CuponUso
from app.models.user import Usuario

# Create all tables
Base.metadata.create_all(bind=engine)

def create_test_coupon():
    db = SessionLocal()
    try:
        # Create a test coupon
        cupon = Cupon(
            codigo='TEST10',
            descripcion='Cupón de prueba 10%',
            tipo_descuento='porcentaje',
            valor=10,
            fecha_inicio=datetime.now() - timedelta(days=1),
            fecha_fin=datetime.now() + timedelta(days=30),
            activo=True
        )
        db.add(cupon)
        db.commit()
        db.refresh(cupon)
        print(f"Cupón creado exitosamente: {cupon.codigo} - {cupon.descripcion}")
        return cupon
    except Exception as e:
        print(f"Error al crear el cupón: {str(e)}")
        db.rollback()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    create_test_coupon()
