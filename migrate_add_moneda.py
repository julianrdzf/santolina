#!/usr/bin/env python3
"""
Script para agregar la columna 'moneda' a la tabla compra_ebooks
Ejecutar: python migrate_add_moneda.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Cargar .env
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

def main():
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("❌ DATABASE_URL no encontrada")
        return
    
    # Crear conexión
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Verificar si la columna ya existe
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'compra_ebooks' AND column_name = 'moneda'
            """))
            
            if result.fetchone():
                print("✅ La columna 'moneda' ya existe en compra_ebooks")
                return
            
            # Agregar columna
            print("🔄 Agregando columna 'moneda' a compra_ebooks...")
            conn.execute(text("""
                ALTER TABLE compra_ebooks 
                ADD COLUMN moneda VARCHAR DEFAULT 'USD' NOT NULL
            """))
            
            # Actualizar registros existentes
            print("🔄 Actualizando registros existentes...")
            result = conn.execute(text("""
                UPDATE compra_ebooks 
                SET moneda = 'USD' 
                WHERE moneda IS NULL
            """))
            
            conn.commit()
            print(f"✅ Migración completada. {result.rowcount} registros actualizados.")
            
    except Exception as e:
        print(f"❌ Error en migración: {e}")
    finally:
        engine.dispose()

if __name__ == "__main__":
    main()
