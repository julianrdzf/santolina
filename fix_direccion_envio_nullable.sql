-- Migración para permitir direccion_envio_id como NULL y agregar metodo_envio_id
-- Esto permite órdenes de retiro sin dirección de envío y tracking del método de envío

-- Permitir NULL en direccion_envio_id
ALTER TABLE ordenes ALTER COLUMN direccion_envio_id DROP NOT NULL;

-- Agregar columna metodo_envio_id
ALTER TABLE ordenes ADD COLUMN metodo_envio_id INTEGER NOT NULL REFERENCES costos_envio(id);

-- Verificar los cambios
\d ordenes;
