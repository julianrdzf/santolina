-- Inicialización de datos base para Santolina
-- Ejecutar manualmente cuando sea necesario inicializar categorías de eventos y métodos de envío

-- ========================================
-- CATEGORÍAS DE EVENTOS
-- ========================================

-- Limpiar categorías existentes (opcional - descomentar si se quiere reinicializar)
-- DELETE FROM categorias_eventos;

-- Insertar categorías principales (nivel 1)
INSERT INTO categorias_eventos (nombre, id_categoria_padre) VALUES 
('Yoga', NULL),
('Alimentación', NULL),
('Terapias', NULL),
('Talleres / cursos', NULL),
('Retiros', NULL);

-- Variables para almacenar los IDs generados automáticamente
-- (En PostgreSQL necesitamos hacer esto paso a paso)

-- Insertar subcategorías de Yoga (nivel 2)
INSERT INTO categorias_eventos (nombre, id_categoria_padre) 
SELECT 'Clases Hatha Yoga', id FROM categorias_eventos WHERE nombre = 'Yoga' AND id_categoria_padre IS NULL;

INSERT INTO categorias_eventos (nombre, id_categoria_padre) 
SELECT 'Yoga & Gong', id FROM categorias_eventos WHERE nombre = 'Yoga' AND id_categoria_padre IS NULL;

INSERT INTO categorias_eventos (nombre, id_categoria_padre) 
SELECT 'Chakras y Yoga', id FROM categorias_eventos WHERE nombre = 'Yoga' AND id_categoria_padre IS NULL;

INSERT INTO categorias_eventos (nombre, id_categoria_padre) 
SELECT 'Sup Yoga', id FROM categorias_eventos WHERE nombre = 'Yoga' AND id_categoria_padre IS NULL;

-- Insertar subcategorías de Alimentación (nivel 2)
INSERT INTO categorias_eventos (nombre, id_categoria_padre) 
SELECT 'Asesoramiento nutricional', id FROM categorias_eventos WHERE nombre = 'Alimentación' AND id_categoria_padre IS NULL;

-- Insertar subcategorías de Terapias (nivel 2)
INSERT INTO categorias_eventos (nombre, id_categoria_padre) 
SELECT 'Reiki', id FROM categorias_eventos WHERE nombre = 'Terapias' AND id_categoria_padre IS NULL;

INSERT INTO categorias_eventos (nombre, id_categoria_padre) 
SELECT 'Péndulo hebreo', id FROM categorias_eventos WHERE nombre = 'Terapias' AND id_categoria_padre IS NULL;

INSERT INTO categorias_eventos (nombre, id_categoria_padre) 
SELECT 'Terapia Floral', id FROM categorias_eventos WHERE nombre = 'Terapias' AND id_categoria_padre IS NULL;

INSERT INTO categorias_eventos (nombre, id_categoria_padre) 
SELECT 'Constelaciones', id FROM categorias_eventos WHERE nombre = 'Terapias' AND id_categoria_padre IS NULL;

INSERT INTO categorias_eventos (nombre, id_categoria_padre) 
SELECT 'Limpieza energética', id FROM categorias_eventos WHERE nombre = 'Terapias' AND id_categoria_padre IS NULL;

-- Insertar sub-subcategorías de Reiki (nivel 3)
INSERT INTO categorias_eventos (nombre, id_categoria_padre) 
SELECT 'Sesión individual', id FROM categorias_eventos WHERE nombre = 'Reiki';

INSERT INTO categorias_eventos (nombre, id_categoria_padre) 
SELECT 'Iniciación en Reiki', id FROM categorias_eventos WHERE nombre = 'Reiki';

-- Insertar sub-subcategorías de Constelaciones (nivel 3)
INSERT INTO categorias_eventos (nombre, id_categoria_padre) 
SELECT 'Sesión individual', id FROM categorias_eventos WHERE nombre = 'Constelaciones';

INSERT INTO categorias_eventos (nombre, id_categoria_padre) 
SELECT 'Sesión grupal', id FROM categorias_eventos WHERE nombre = 'Constelaciones';

-- Insertar sub-subcategorías de Limpieza energética (nivel 3)
INSERT INTO categorias_eventos (nombre, id_categoria_padre) 
SELECT 'Sesión individual', id FROM categorias_eventos WHERE nombre = 'Limpieza energética';

INSERT INTO categorias_eventos (nombre, id_categoria_padre) 
SELECT 'Limpieza de espacios', id FROM categorias_eventos WHERE nombre = 'Limpieza energética';

-- Insertar subcategorías de Talleres / cursos (nivel 2)
INSERT INTO categorias_eventos (nombre, id_categoria_padre) 
SELECT 'Ritual del útero', id FROM categorias_eventos WHERE nombre = 'Talleres / cursos' AND id_categoria_padre IS NULL;

INSERT INTO categorias_eventos (nombre, id_categoria_padre) 
SELECT 'Taller online de limpieza energética', id FROM categorias_eventos WHERE nombre = 'Talleres / cursos' AND id_categoria_padre IS NULL;

-- ========================================
-- MÉTODOS DE ENVÍO
-- ========================================

-- Limpiar métodos de envío existentes (opcional - descomentar si se quiere reinicializar)
-- DELETE FROM costos_envio;

-- Insertar métodos de envío
INSERT INTO costos_envio (nombre, descripcion, costo, activo, requiere_direccion, url_imagen) VALUES 
('Retiro zona Aguada-Reducto', 'Coordinar con el vendedor para retirar el producto.', 0, true, false, NULL),
('Envío por agencia de transporte', 'Costo del envío a cargo del cliente mediante DAC, UES u otra preferencia del comprador.', 0, true, true, NULL);

-- ========================================
-- VERIFICACIONES
-- ========================================

-- Verificar categorías de eventos
SELECT 
    c1.id,
    c1.nombre as categoria,
    c2.nombre as subcategoria,
    c3.nombre as sub_subcategoria
FROM categorias_eventos c1
LEFT JOIN categorias_eventos c2 ON c2.id_categoria_padre = c1.id
LEFT JOIN categorias_eventos c3 ON c3.id_categoria_padre = c2.id
WHERE c1.id_categoria_padre IS NULL
ORDER BY c1.id, c2.id, c3.id;

-- Verificar métodos de envío
SELECT 
    id,
    nombre,
    descripcion,
    costo,
    activo,
    requiere_direccion
FROM costos_envio
ORDER BY id;
