-- =====================================================
-- Script de Inicialización de Base de Datos
-- Sistema de Reclutamiento
-- =====================================================

-- Crear base de datos
CREATE DATABASE IF NOT EXISTS reclutamiento CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE reclutamiento;

-- =====================================================
-- TABLA: roles
-- =====================================================
CREATE TABLE IF NOT EXISTS roles (
    id_rol INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion TEXT,
    KEY idx_nombre (nombre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insertar roles (compatible con MySQL y SQLite)
INSERT OR IGNORE INTO roles (id_rol, nombre, descripcion) VALUES
(1, 'admin', 'Administrador del sistema - Acceso completo'),
(2, 'reclutador', 'Reclutador - Gestión de cargos, candidatos y postulaciones'),
(3, 'gerente', 'Gerente de RRHH - Visualización de reportes'),
(4, 'candidato', 'Candidato - Registro y seguimiento de postulaciones');

-- =====================================================
-- TABLA: usuarios
-- =====================================================
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario INT PRIMARY KEY AUTO_INCREMENT,
    nombre_usuario VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    rol_id INT NOT NULL,
    activo BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultimo_acceso TIMESTAMP NULL,
    FOREIGN KEY (rol_id) REFERENCES roles(id_rol),
    INDEX idx_nombre_usuario (nombre_usuario),
    INDEX idx_email (email),
    INDEX idx_rol (rol_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABLA: cargos
-- =====================================================
CREATE TABLE IF NOT EXISTS cargos (
    id_cargo INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    departamento VARCHAR(100),
    salario_minimo DECIMAL(10,2),
    salario_maximo DECIMAL(10,2),
    tipo_contrato VARCHAR(50),
    ubicacion VARCHAR(100),
    estado VARCHAR(50) DEFAULT 'Activo',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_cierre DATE,
    INDEX idx_estado (estado),
    INDEX idx_departamento (departamento)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABLA: candidatos
-- =====================================================
CREATE TABLE IF NOT EXISTS candidatos (
    cedula VARCHAR(10) PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    telefono VARCHAR(20),
    resumen TEXT,
    habilidades TEXT,
    experiencia_anos INT DEFAULT 0,
    nivel_educativo VARCHAR(100),
    ubicacion VARCHAR(100),
    disponibilidad VARCHAR(50),
    salario_esperado DECIMAL(10,2),
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activo BOOLEAN DEFAULT 1,
    INDEX idx_cedula (cedula),
    INDEX idx_email (email),
    INDEX idx_activo (activo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABLA: referencias_personales
-- =====================================================
CREATE TABLE IF NOT EXISTS referencias_personales (
    id INT PRIMARY KEY AUTO_INCREMENT,
    cedula VARCHAR(10) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    telefono VARCHAR(20),
    relacion VARCHAR(50),
    descripcion TEXT,
    FOREIGN KEY (cedula) REFERENCES candidatos(cedula) ON DELETE CASCADE,
    INDEX idx_cedula (cedula)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABLA: licencias
-- =====================================================
CREATE TABLE IF NOT EXISTS licencias (
    id_licencia INT PRIMARY KEY AUTO_INCREMENT,
    cedula VARCHAR(10) NOT NULL,
    tipo VARCHAR(100) NOT NULL,
    fecha_vencimiento DATE,
    estado VARCHAR(50),
    FOREIGN KEY (cedula) REFERENCES candidatos(cedula) ON DELETE CASCADE,
    INDEX idx_cedula (cedula)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABLA: postulaciones
-- =====================================================
CREATE TABLE IF NOT EXISTS postulaciones (
    id_postulacion INT PRIMARY KEY AUTO_INCREMENT,
    cedula VARCHAR(10) NOT NULL,
    id_cargo INT NOT NULL,
    fecha_postulacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado VARCHAR(50) DEFAULT 'Recibido',
    fuente_reclutamiento VARCHAR(100),
    notas TEXT,
    puntaje_evaluacion INT,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (cedula) REFERENCES candidatos(cedula) ON DELETE CASCADE,
    FOREIGN KEY (id_cargo) REFERENCES cargos(id_cargo) ON DELETE CASCADE,
    UNIQUE KEY uk_candidato_cargo (cedula, id_cargo),
    INDEX idx_cedula (cedula),
    INDEX idx_cargo (id_cargo),
    INDEX idx_estado (estado)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABLA: experiencias
-- =====================================================
CREATE TABLE IF NOT EXISTS experiencias (
    id_experiencia INT PRIMARY KEY AUTO_INCREMENT,
    cedula VARCHAR(10) NOT NULL,
    empresa VARCHAR(100) NOT NULL,
    cargo VARCHAR(100) NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE,
    actual BOOLEAN DEFAULT 0,
    descripcion TEXT,
    FOREIGN KEY (cedula) REFERENCES candidatos(cedula) ON DELETE CASCADE,
    INDEX idx_cedula (cedula)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABLA: documentos
-- =====================================================
CREATE TABLE IF NOT EXISTS documentos (
    id_documento INT PRIMARY KEY AUTO_INCREMENT,
    id_postulacion INT,
    nombre_archivo VARCHAR(255),
    ruta_archivo VARCHAR(500),
    fecha_subida TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_postulacion) REFERENCES postulaciones(id_postulacion) ON DELETE CASCADE,
    INDEX idx_postulacion (id_postulacion)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- DATOS DE EJEMPLO
-- =====================================================

-- Usuarios de ejemplo (compatible con MySQL y SQLite)
INSERT OR IGNORE INTO usuarios (nombre_usuario, email, password_hash, rol_id) VALUES
('admin', 'admin@reclutamiento.com', 'pbkdf2:sha256:260000$salt$hash', 1),
('reclutador1', 'reclutador@reclutamiento.com', 'pbkdf2:sha256:260000$salt$hash', 2);

-- Cargos de ejemplo (compatible con MySQL y SQLite)
INSERT OR IGNORE INTO cargos (nombre, descripcion, departamento, salario_minimo, salario_maximo, tipo_contrato) VALUES
('Desarrollador Python', 'Desarrollo de aplicaciones web con Python y Django', 'Tecnología', 15000.00, 25000.00, 'Tiempo Completo'),
('Analista de RRHH', 'Gestión de procesos de reclutamiento y selección', 'Recursos Humanos', 12000.00, 18000.00, 'Tiempo Completo'),
('Diseñador UX/UI', 'Diseño de interfaces y experiencia de usuario', 'Diseño', 13000.00, 20000.00, 'Tiempo Completo');

-- Candidatos de ejemplo (compatible con MySQL y SQLite)
INSERT OR IGNORE INTO candidatos (cedula, nombre, apellido, email, telefono, resumen, habilidades, experiencia_anos, nivel_educativo, ubicacion, disponibilidad, salario_esperado) VALUES
('1234567890', 'Juan', 'Pérez', 'juan.perez@email.com', '555-1234', 'Desarrollador con 5 años de experiencia', 'Python,Django,JavaScript,React', 5, 'Universitario', 'Quito', 'Inmediata', 20000.00),
('0987654321', 'María', 'García', 'maria.garcia@email.com', '555-5678', 'Diseñadora especializada en UX/UI', 'Figma,Adobe XD,Sketch,Photoshop', 3, 'Universitario', 'Guayaquil', '2 semanas', 18000.00);

-- Postulaciones de ejemplo (compatible con MySQL y SQLite)
INSERT OR IGNORE INTO postulaciones (cedula, id_cargo, estado, fuente_reclutamiento) VALUES
('1234567890', 1, 'En revisión', 'LinkedIn'),
('0987654321', 3, 'Recibido', 'Sitio web');

-- Experiencias de ejemplo (compatible con MySQL y SQLite)
INSERT OR IGNORE INTO experiencias (cedula, empresa, cargo, fecha_inicio, fecha_fin, actual, descripcion) VALUES
('1234567890', 'Tech Solutions', 'Desarrollador Junior', '2019-01-15', '2021-06-30', 0, 'Desarrollo de aplicaciones web'),
('1234567890', 'Digital Agency', 'Desarrollador Python', '2021-07-01', '2024-12-31', 1, 'Desarrollo con Django y Flask'),
('0987654321', 'Design Studio', 'Diseñadora UX', '2021-03-01', '2023-08-31', 0, 'Diseño de aplicaciones móviles'),
('0987654321', 'Creative Agency', 'Diseñadora UX/UI Senior', '2023-09-01', '2024-12-31', 1, 'Liderazgo en proyectos de diseño');

PRINT '✅ Base de datos reclutamiento inicializada correctamente';
