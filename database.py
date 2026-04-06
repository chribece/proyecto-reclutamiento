import pymysql
import sqlite3
from contextlib import contextmanager
from config import Config, get_mysql_config
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
        
        # Determinar si usamos MySQL o SQLite
        self.mysql_config = get_mysql_config()
        self.use_mysql = self.mysql_config is not None
        
        if self.use_mysql:
            # Configuración para MySQL/MariaDB
            self.config = self.mysql_config
        else:
            # Configuración para SQLite (fallback)
            self.sqlite_db_path = 'reclutamiento.db'
        
        self._initialized = True
    
    @contextmanager
    def get_connection(self):
        """Obtiene una conexión a la base de datos (MySQL o SQLite)"""
        conn = None
        try:
            if self.use_mysql:
                # Conexión MySQL
                conn = pymysql.connect(**self.config)
            else:
                # Conexión SQLite
                conn = sqlite3.connect(self.sqlite_db_path)
                conn.row_factory = sqlite3.Row  # Para que los resultados se comporten como diccionarios
            
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
            if self.use_mysql:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS roles (
                        id_rol INT PRIMARY KEY AUTO_INCREMENT,
                        nombre VARCHAR(50) NOT NULL UNIQUE,
                        descripcion TEXT
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                ''')
            else:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS roles (
                        id_rol INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre TEXT NOT NULL UNIQUE,
                        descripcion TEXT
                    )
                ''')
            
            # Insertar roles por defecto
            cursor.execute("INSERT IGNORE INTO roles (nombre, descripcion) VALUES ('admin', 'Administrador del sistema')")
            cursor.execute("INSERT IGNORE INTO roles (nombre, descripcion) VALUES ('reclutador', 'Reclutador')")
            cursor.execute("INSERT IGNORE INTO roles (nombre, descripcion) VALUES ('gerente', 'Gerente de RRHH')")
            cursor.execute("INSERT IGNORE INTO roles (nombre, descripcion) VALUES ('candidato', 'Candidato')")
            
            # Tabla Usuarios
            if self.use_mysql:
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
            else:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS usuarios (
                        id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre_usuario TEXT NOT NULL UNIQUE,
                        email TEXT NOT NULL UNIQUE,
                        password_hash TEXT NOT NULL,
                        rol_id INTEGER NOT NULL,
                        activo INTEGER DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        ultimo_acceso TIMESTAMP NULL,
                        FOREIGN KEY (rol_id) REFERENCES roles(id_rol)
                    )
                ''')
            
            # Tabla Estudios
            if self.use_mysql:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS estudios (
                        id_estudio INT PRIMARY KEY AUTO_INCREMENT,
                        nivel_estudio VARCHAR(100) NOT NULL
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                ''')
            else:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS estudios (
                        id_estudio INTEGER PRIMARY KEY AUTOINCREMENT,
                        nivel_estudio TEXT NOT NULL
                    )
                ''')
            
            # Tabla de Estados de Estudio
            if self.use_mysql:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cat_estado_estudio (
                        id_estado INT PRIMARY KEY AUTO_INCREMENT,
                        codigo VARCHAR(50) NOT NULL,
                        descripcion VARCHAR(100) NOT NULL
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                ''')
            else:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cat_estado_estudio (
                        id_estado INTEGER PRIMARY KEY AUTOINCREMENT,
                        codigo TEXT NOT NULL,
                        descripcion TEXT NOT NULL
                    )
                ''')
            
            # Tabla Teléfonos
            if self.use_mysql:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS telefonos (
                        id_telefono INT PRIMARY KEY AUTO_INCREMENT,
                        numero VARCHAR(20) NOT NULL,
                        tipo VARCHAR(50)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                ''')
            else:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS telefonos (
                        id_telefono INTEGER PRIMARY KEY AUTOINCREMENT,
                        numero TEXT NOT NULL,
                        tipo TEXT
                    )
                ''')
            
            # Tabla Candidatos
            if self.use_mysql:
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
                        INDEX idx_cedula (cedula),
                        INDEX idx_email (email)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                ''')
            else:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS candidatos (
                        cedula TEXT PRIMARY KEY,
                        nombre TEXT NOT NULL,
                        apellido TEXT NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        resumen TEXT,
                        habilidades TEXT,
                        experiencia_anos INTEGER DEFAULT 0,
                        nivel_educativo TEXT,
                        direccion_domicilio TEXT,
                        disponibilidad TEXT,
                        salario_esperado REAL,
                        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        activo INTEGER DEFAULT 1
                    )
                ''')
            
            # Tabla Referencias Personales
            if self.use_mysql:
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
            else:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS referencias_personales (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cedula TEXT NOT NULL,
                        nombre TEXT NOT NULL,
                        telefono TEXT,
                        relacion TEXT,
                        descripcion TEXT,
                        FOREIGN KEY (cedula) REFERENCES candidatos(cedula) ON DELETE CASCADE
                    )
                ''')
            
            # Tabla Licencias
            if self.use_mysql:
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
            else:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS licencias (
                        id_licencia INTEGER PRIMARY KEY AUTOINCREMENT,
                        cedula TEXT NOT NULL,
                        tipo TEXT NOT NULL,
                        fecha_vencimiento DATE,
                        estado TEXT,
                        FOREIGN KEY (cedula) REFERENCES candidatos(cedula) ON DELETE CASCADE
                    )
                ''')
            
            # Tabla Estados de Licencia
            if self.use_mysql:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cat_estado_licencia (
                        id_estado INT PRIMARY KEY AUTO_INCREMENT,
                        codigo VARCHAR(50) NOT NULL,
                        descripcion VARCHAR(100) NOT NULL
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                ''')
            else:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cat_estado_licencia (
                        id_estado INTEGER PRIMARY KEY AUTOINCREMENT,
                        codigo TEXT NOT NULL,
                        descripcion TEXT NOT NULL
                    )
                ''')
            
            # Tabla Cargos/Vacantes
            if self.use_mysql:
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
            else:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cargos (
                        id_cargo INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre TEXT NOT NULL,
                        descripcion TEXT,
                        departamento TEXT,
                        salario_minimo REAL,
                        salario_maximo REAL,
                        tipo_contrato TEXT,
                        direccion_domicilio TEXT,
                        estado TEXT DEFAULT 'Activo',
                        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        fecha_cierre DATE
                    )
                ''')
            
            # Tabla Postulaciones
            if self.use_mysql:
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
            else:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS postulaciones (
                        id_postulacion INTEGER PRIMARY KEY AUTOINCREMENT,
                        cedula TEXT NOT NULL,
                        id_cargo INTEGER NOT NULL,
                        fecha_postulacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        estado TEXT DEFAULT 'Recibido',
                        fuente_reclutamiento TEXT,
                        notas TEXT,
                        puntaje_evaluacion INTEGER,
                        fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (cedula) REFERENCES candidatos(cedula) ON DELETE CASCADE,
                        FOREIGN KEY (id_cargo) REFERENCES cargos(id_cargo) ON DELETE CASCADE,
                        UNIQUE (cedula, id_cargo)
                    )
                ''')
            
            # Tabla Estados Postulación
            if self.use_mysql:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cat_estado_postulacion (
                        id_estado INT PRIMARY KEY AUTO_INCREMENT,
                        codigo VARCHAR(50) NOT NULL,
                        descripcion VARCHAR(100) NOT NULL
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                ''')
            else:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cat_estado_postulacion (
                        id_estado INTEGER PRIMARY KEY AUTOINCREMENT,
                        codigo TEXT NOT NULL,
                        descripcion TEXT NOT NULL
                    )
                ''')
            
            # Tabla Historial
            if self.use_mysql:
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
            else:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS historial (
                        id_historial INTEGER PRIMARY KEY AUTOINCREMENT,
                        id_postulacion INTEGER NOT NULL,
                        estado TEXT,
                        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        descripcion TEXT,
                        FOREIGN KEY (id_postulacion) REFERENCES postulaciones(id_postulacion) ON DELETE CASCADE
                    )
                ''')
            
            # Tabla Documentos
            if self.use_mysql:
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
            else:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS documentos (
                        id_documento INTEGER PRIMARY KEY AUTOINCREMENT,
                        id_postulacion INTEGER,
                        id_tipo INTEGER,
                        nombre_archivo TEXT,
                        ruta_archivo TEXT,
                        fecha_subida TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (id_postulacion) REFERENCES postulaciones(id_postulacion) ON DELETE CASCADE,
                        FOREIGN KEY (id_tipo) REFERENCES cat_tipo_documento(id_tipo)
                    )
                ''')
            
            # Tabla Tipos de Documento
            if self.use_mysql:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cat_tipo_documento (
                        id_tipo INT PRIMARY KEY AUTO_INCREMENT,
                        codigo VARCHAR(50) NOT NULL,
                        descripcion VARCHAR(100) NOT NULL
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                ''')
            else:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cat_tipo_documento (
                        id_tipo INTEGER PRIMARY KEY AUTOINCREMENT,
                        codigo TEXT NOT NULL,
                        descripcion TEXT NOT NULL
                    )
                ''')
            
            # Tabla Experiencia Laboral
            if self.use_mysql:
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
            else:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS experiencias (
                        id_experiencia INTEGER PRIMARY KEY AUTOINCREMENT,
                        cedula TEXT NOT NULL,
                        empresa TEXT NOT NULL,
                        cargo TEXT NOT NULL,
                        fecha_inicio DATE NOT NULL,
                        fecha_fin DATE,
                        actual INTEGER DEFAULT 0,
                        descripcion TEXT,
                        FOREIGN KEY (cedula) REFERENCES candidatos(cedula) ON DELETE CASCADE
                    )
                ''')
            
            conn.commit()

# Instancia singleton
db = DatabaseManager()