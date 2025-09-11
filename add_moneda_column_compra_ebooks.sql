-- Agregar columna 'moneda' a la tabla compra_ebooks
-- Ejecutar este script en pgAdmin

ALTER TABLE compra_ebooks 
ADD COLUMN moneda VARCHAR DEFAULT 'USD' NOT NULL;

-- Actualizar registros existentes para establecer USD como moneda por defecto
UPDATE compra_ebooks 
SET moneda = 'USD' 
WHERE moneda IS NULL;

-- Comentario: 
-- Esta columna almacenará la moneda en la que se procesó efectivamente el pago
-- USD: PayPal y ebooks originalmente en dólares
-- UYU: MercadoPago cuando convierte automáticamente a pesos uruguayos
-- Otras monedas según la configuración de MercadoPago
