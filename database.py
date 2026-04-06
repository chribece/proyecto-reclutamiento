import pymysql
from contextlib import contextmanager
from config import Config
from datetime import datetime

class DatabaseManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self.config = {
            'host': Config.DB_HOST,
            'port': Config.DB_PORT,
            'user': Config.DB_USER,
            'password': Config.DB_PASSWORD or '',
            'database': Config.DB_NAME,
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }
        self._initialized = True
    
    @contextmanager
    def get_connection(self):
        conn = None
        try:
            conn = pymysql.connect(**self.config)
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    def init_database(self):
        """Inicializa todas las tablas de la base de datos"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabla Roles
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS roles (
                    id_rol INT PRIMARY KEY AUTO_INCREMENT,
                    nombre VARCHAR(50) NOT NULL UNIQUE,
                    descripcion TEXT
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            # Insertar roles por defecto
            cursor.execute("INSERT IGNORE INTO roles (nombre, descripcion) VALUES ('admin', 'Administrador del sistema')")
            cursor.execute("INSERT IGNORE INTO roles (nombre, descripcion) VALUES ('reclutador', 'Reclutador')")
            cursor.execute("INSERT IGNORE INTO roles (nombre, descripcion) VALUES ('gerente', 'Gerente de RRHH')")
            cursor.execute("INSERT IGNORE INTO roles (nombre, descripcion) VALUES ('candidato', 'Candidato')")
            
            # Tabla Usuarios
            cursor.execute('''
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
                    INDEX idx_email (email)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            # Tabla Estudios
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS estudios (
                    id_estudio INT PRIMARY KEY AUTO_INCREMENT,
                    nivel_estudio VARCHAR(100) NOT NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            # Tabla de Estados de Estudio
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cat_estado_estudio (
                    id_estado INT PRIMARY KEY AUTO_INCREMENT,
                    codigo VARCHAR(50) NOT NULL,
                    descripcion VARCHAR(100) NOT NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            # Tabla Teléfonos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS telefonos (
                    id_telefono INT PRIMARY KEY AUTO_INCREMENT,
                    numero VARCHAR(20) NOT NULL,
                    tipo VARCHAR(50)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            # Tabla Candidatos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS candidatos (
                    cedula VARCHAR(10) PRIMARY KEY,
                    nombre VARCHAR(100) NOT NULL,
                    apellido VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    resumen TEXT,
                    habilidades TEXT,
                    experiencia_anos INT DEFAULT 0,
                    nivel_educativo VARCHAR(100),
                    direccion_domicilio VARCHAR(100),
                    disponibilidad VARCHAR(50),
                    salario_esperado DECIMAL(10,2),
                    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    activo BOOLEAN DEFAULT 1,
                    index idx_cedula (cedula),
                    INDEX idx_email (email)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            # Tabla Referencias Personales
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS referencias_personales (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    cedula VARCHAR(10) NOT NULL,
                    nombre VARCHAR(100) NOT NULL,
                    telefono VARCHAR(20),
                    relacion VARCHAR(50),
                    descripcion TEXT,
                    FOREIGN KEY (cedula) REFERENCES candidatos(cedula) ON DELETE CASCADE,
                    INDEX idx_cedula (cedula)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            # Tabla Licencias
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS licencias (
                    id_licencia INT PRIMARY KEY AUTO_INCREMENT,
                    cedula VARCHAR(10) NOT NULL,
                    tipo VARCHAR(100) NOT NULL,
                    fecha_vencimiento DATE,
                    estado VARCHAR(50),
                    FOREIGN KEY (cedula) REFERENCES candidatos(cedula) ON DELETE CASCADE,
                    INDEX idx_cedula (cedula)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            # Tabla Estados de Licencia
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cat_estado_licencia (
                    id_estado INT PRIMARY KEY AUTO_INCREMENT,
                    codigo VARCHAR(50) NOT NULL,
                    descripcion VARCHAR(100) NOT NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            # Tabla Cargos/Vacantes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cargos (
                    id_cargo INT PRIMARY KEY AUTO_INCREMENT,
                    nombre VARCHAR(100) NOT NULL,
                    descripcion TEXT,
                    departamento VARCHAR(100),
                    salario_minimo DECIMAL(10,2),
                    salario_maximo DECIMAL(10,2),
                    tipo_contrato VARCHAR(50),
                    direccion_domicilio VARCHAR(100),
                    estado VARCHAR(50) DEFAULT 'Activo',
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_cierre DATE,
                    INDEX idx_estado (estado)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            # Tabla Postulaciones
            cursor.execute('''
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
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            # Tabla Estados Postulación
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cat_estado_postulacion (
                    id_estado INT PRIMARY KEY AUTO_INCREMENT,
                    codigo VARCHAR(50) NOT NULL,
                    descripcion VARCHAR(100) NOT NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            # Tabla Historial
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS historial (
                    id_historial INT PRIMARY KEY AUTO_INCREMENT,
                    id_postulacion INT NOT NULL,
                    estado VARCHAR(50),
                    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    descripcion TEXT,
                    FOREIGN KEY (id_postulacion) REFERENCES postulaciones(id_postulacion) ON DELETE CASCADE,
                    INDEX idx_postulacion (id_postulacion)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            # Tabla Documentos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS documentos (
                    id_documento INT PRIMARY KEY AUTO_INCREMENT,
                    id_postulacion INT,
                    id_tipo INT,
                    nombre_archivo VARCHAR(255),
                    ruta_archivo VARCHAR(500),
                    fecha_subida TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (id_postulacion) REFERENCES postulaciones(id_postulacion) ON DELETE CASCADE,
                    FOREIGN KEY (id_tipo) REFERENCES cat_tipo_documento(id_tipo),
                    INDEX idx_postulacion (id_postulacion)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            # Tabla Tipos de Documento
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cat_tipo_documento (
                    id_tipo INT PRIMARY KEY AUTO_INCREMENT,
                    codigo VARCHAR(50) NOT NULL,
                    descripcion VARCHAR(100) NOT NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            # Tabla Experiencia Laboral
            cursor.execute('''
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
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            conn.commit()

# Instancia singleton
db = DatabaseManager()