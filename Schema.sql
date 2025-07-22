-- schema.sql (Versión 2)

DROP TABLE IF EXISTS orden;
DROP TABLE IF EXISTS requerimiento;
DROP TABLE IF EXISTS proveedor;

-- NUEVA TABLA: Proveedores
CREATE TABLE proveedor (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    ruc TEXT, -- Opcional: RUC o identificador fiscal
    contacto TEXT -- Opcional: Nombre o email de contacto
);

-- Tabla de Requerimientos MODIFICADA
CREATE TABLE requerimiento (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_requerimiento TEXT NOT NULL UNIQUE,
    descripcion TEXT NOT NULL,
    fecha_presentacion TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'En Mesa de Partes',
    -- NUEVO CAMPO: para guardar el nombre del archivo subido
    archivo_path TEXT
);

-- Tabla de Órdenes MODIFICADA
CREATE TABLE orden (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    requerimiento_id INTEGER NOT NULL,
    proveedor_id INTEGER NOT NULL,
    monto REAL,
    tipo_orden TEXT NOT NULL,
    fecha_emision TEXT NOT NULL,
    fecha_notificacion TEXT NOT NULL,
    plazo_ejecucion_dias INTEGER NOT NULL,
    archivo_orden_path TEXT, -- <--- NUEVA COLUMNA (puede ser NULL)
    FOREIGN KEY (requerimiento_id) REFERENCES requerimiento (id),
    FOREIGN KEY (proveedor_id) REFERENCES proveedor (id)
);