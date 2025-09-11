-- CREACIÓN DESDE CERO: Sistema de eventos reestructurado
-- Ejecutar estos comandos en orden en pgAdmin después de eliminar las tablas viejas

-- 1. Eliminar tablas existentes (si existen)
DROP TABLE IF EXISTS reservas CASCADE;
DROP TABLE IF EXISTS eventos CASCADE;

-- 2. Crear tabla eventos (estructura simplificada)
CREATE TABLE eventos (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR NOT NULL,
    descripcion VARCHAR,
    categoria_id INTEGER REFERENCES categorias_eventos(id),
    ubicacion VARCHAR,
    direccion VARCHAR,
    costo NUMERIC(10, 2),
    imagen VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Crear tabla fechas_evento
CREATE TABLE fechas_evento (
    id SERIAL PRIMARY KEY,
    evento_id INTEGER NOT NULL REFERENCES eventos(id) ON DELETE CASCADE,
    fecha DATE NOT NULL
);

-- 4. Crear tabla horarios_fecha_evento
CREATE TABLE horarios_fecha_evento (
    id SERIAL PRIMARY KEY,
    fecha_evento_id INTEGER NOT NULL REFERENCES fechas_evento(id) ON DELETE CASCADE,
    hora_inicio TIME NOT NULL,
    duracion_minutos INTEGER NOT NULL,
    cupos INTEGER NOT NULL
);

-- 5. Crear tabla reservas (nueva estructura)
CREATE TABLE reservas (
    id SERIAL PRIMARY KEY,
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    horario_id INTEGER NOT NULL REFERENCES horarios_fecha_evento(id) ON DELETE CASCADE,
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    cupos INTEGER NOT NULL,
    estado_pago VARCHAR DEFAULT 'pendiente' NOT NULL,
    transaction_id VARCHAR NULL
);

-- 6. Crear índices para mejor rendimiento
CREATE INDEX idx_eventos_categoria_id ON eventos(categoria_id);
CREATE INDEX idx_eventos_created_at ON eventos(created_at);

CREATE INDEX idx_fechas_evento_evento_id ON fechas_evento(evento_id);
CREATE INDEX idx_fechas_evento_fecha ON fechas_evento(fecha);

CREATE INDEX idx_horarios_fecha_evento_fecha_evento_id ON horarios_fecha_evento(fecha_evento_id);
CREATE INDEX idx_horarios_fecha_evento_hora_inicio ON horarios_fecha_evento(hora_inicio);

CREATE INDEX idx_reservas_usuario_id ON reservas(usuario_id);
CREATE INDEX idx_reservas_horario_id ON reservas(horario_id);
CREATE INDEX idx_reservas_estado_pago ON reservas(estado_pago);
CREATE INDEX idx_reservas_fecha_creacion ON reservas(fecha_creacion);

-- 7. Datos de ejemplo (opcional)
-- Insertar un evento de ejemplo:
-- INSERT INTO eventos (titulo, descripcion, ubicacion, costo) 
-- VALUES ('Evento de Prueba', 'Descripción del evento', 'Ubicación de prueba', 50.00);

-- Insertar una fecha para el evento:
-- INSERT INTO fechas_evento (evento_id, fecha) VALUES (1, '2024-12-01');

-- Insertar horarios para la fecha:
-- INSERT INTO horarios_fecha_evento (fecha_evento_id, hora_inicio, duracion_minutos, cupos) 
-- VALUES (1, '10:00:00', 120, 20);

-- NOTAS:
-- 1. Este script elimina completamente las tablas existentes
-- 2. Se perderán todos los datos existentes
-- 3. Asegúrate de tener backup si necesitas conservar algún dato
-- 4. La tabla usuarios debe existir previamente para las foreign keys
