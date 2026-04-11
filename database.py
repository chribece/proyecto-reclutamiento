import pymysql
import sqlite3
import psycopg2
from contextlib import contextmanager
from config import Config, get_mysql_config
from datetime import datetime
import os

class UniversalCursor:
    """
    Cursor wrapper que traduce automáticamente placeholders de MySQL (%s) a SQLite (?)
    y convierte resultados a diccionarios para compatibilidad universal
    """
    def __init__(self, cursor, db_type):
        self.cursor = cursor
        self.db_type = db_type
    
    def _convert_query(self, query):
        """Convierte placeholders según el tipo de base de datos"""
        if self.db_type == 'sqlite':
            import re
            # Reemplazar %s por ? para SQLite (solo placeholders, no literales)
            query = re.sub(r'(?<!\\)%s', '?', query)
        # PostgreSQL y MySQL usan %s como placeholder, no necesitan conversión
        return query
    
    def _convert_result(self, result):
        """Convierte sqlite3.Row a diccionario para compatibilidad"""
        if self.db_type == 'sqlite' and hasattr(result, 'keys'):
            # Es un sqlite3.Row, convertir a dict
            return dict(result)
        return result
    
    def execute(self, query, params=None):
        """Intercepta todas las llamadas a execute() y traduce si es necesario"""
        converted_query = self._convert_query(query)
        if params:
            return self.cursor.execute(converted_query, params)
        else:
            return self.cursor.execute(converted_query)
    
    def executemany(self, query, params=None):
        """Intercepta llamadas a executemany()"""
        converted_query = self._convert_query(query)
        if params:
            return self.cursor.executemany(converted_query, params)
        else:
            return self.cursor.executemany(converted_query)
    
    def fetchone(self):
        """Convierte el resultado a diccionario si es necesario"""
        result = self.cursor.fetchone()
        return self._convert_result(result)
    
    def fetchall(self):
        """Convierte todos los resultados a diccionarios si es necesario"""
        results = self.cursor.fetchall()
        if self.db_type == 'sqlite':
            return [self._convert_result(row) for row in results]
        return results
    
    def fetchmany(self, size=None):
        """Convierte múltiples resultados a diccionarios si es necesario"""
        results = self.cursor.fetchmany(size) if size else self.cursor.fetchmany()
        if self.db_type == 'sqlite':
            return [self._convert_result(row) for row in results]
        return results
    
    def __getattr__(self, name):
        """Delega todos los demás métodos al cursor original"""
        return getattr(self.cursor, name)

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
        
        # Determinar tipo de base de datos
        database_url = os.environ.get('DATABASE_URL', '')
        self.mysql_config = get_mysql_config()
        self.use_mysql = self.mysql_config is not None
        self.use_postgresql = 'postgresql://' in database_url
        
        if self.use_postgresql:
            # Configuración para PostgreSQL (Render)
            self.config = database_url
            self.db_type = 'postgresql'
        elif self.use_mysql:
            # Configuración para MySQL/MariaDB
            self.config = self.mysql_config
            self.db_type = 'mysql'
        else:
            # Configuración para SQLite (fallback)
            self.sqlite_db_path = os.environ.get('SQLITE_DB_PATH', 'reclutamiento.db')
            self.db_type = 'sqlite'
        
        self._initialized = True
    
    def _convert_placeholders(self, query: str) -> str:
        """
        Convierte placeholders de MySQL (%s) a SQLite (?) automáticamente
        """
        if self.db_type == 'sqlite':
            # Reemplazar %s por ? para SQLite, pero cuidado con %s dentro de strings
            # Dividimos la consulta en partes para no reemplazar %s literales
            import re
            # Usamos regex para encontrar %s que no están dentro de comillas
            # Esta es una solución simple que funciona para la mayoría de casos
            # Para casos complejos, se podría mejorar con parsing más sofisticado
            query = re.sub(r'(?<!\\)%s', '?', query)
        return query
    
    def _cursor_execute(self, cursor, query: str, params=None):
        """
        Método wrapper para ejecutar consultas con placeholders compatibles
        """
        # Convertir placeholders si es SQLite
        converted_query = self._convert_placeholders(query)
        
        # Ejecutar la consulta
        if params:
            cursor.execute(converted_query, params)
        else:
            cursor.execute(converted_query)
    
    @contextmanager
    def get_connection(self):
        """Obtiene una conexión a la base de datos (MySQL, PostgreSQL o SQLite) con cursor universal"""
        conn = None
        try:
            if self.use_postgresql:
                # Conexión PostgreSQL con cursor para resultados como diccionarios
                conn = psycopg2.connect(self.config)
                # PostgreSQL usa %s como placeholder, no necesita conversión
            elif self.use_mysql:
                # Conexión MySQL con DictCursor para resultados como diccionarios
                conn = pymysql.connect(
                    cursorclass=pymysql.cursors.DictCursor,
                    **self.config
                )
            else:
                # Conexión SQLite con row_factory para resultados como diccionarios
                conn = sqlite3.connect(self.sqlite_db_path)
                conn.row_factory = sqlite3.Row  # Para que los resultados se comporten como diccionarios
            
            # Crear un wrapper para la conexión que devuelva cursores universales
            class UniversalConnection:
                def __init__(self, connection, db_type):
                    self.connection = connection
                    self.db_type = db_type
                
                def cursor(self):
                    """Devuelve un cursor universal que traduce placeholders automáticamente"""
                    if self.db_type == 'postgresql':
                        # PostgreSQL con cursor de diccionarios
                        import psycopg2.extras
                        original_cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                    else:
                        original_cursor = self.connection.cursor()
                    return UniversalCursor(original_cursor, self.db_type)
                
                def commit(self):
                    return self.connection.commit()
                
                def rollback(self):
                    return self.connection.rollback()
                
                def close(self):
                    return self.connection.close()
                
                def __getattr__(self, name):
                    """Delega todos los demás métodos a la conexión original"""
                    return getattr(self.connection, name)
            
            # Envolver la conexión con nuestro traductor universal
            universal_conn = UniversalConnection(conn, self.db_type)
            
            yield universal_conn
            universal_conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    @contextmanager
    def get_cursor(self):
        """Obtiene un cursor con manejo automático de placeholders"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
            finally:
                cursor.close()
    
    def ejecutar_consulta(self, query: str, params=None, fetch_one=False, fetch_all=False):
        """
        Método unificado para ejecutar consultas con compatibilidad MySQL/SQLite
        """
        with self.get_cursor() as cursor:
            self._cursor_execute(cursor, query, params)
            
            if fetch_one:
                result = cursor.fetchone()
                # Convertir sqlite.Row a dict si es necesario
                if self.db_type == 'sqlite' and isinstance(result, sqlite3.Row):
                    result = dict(result)
                return result
            elif fetch_all:
                results = cursor.fetchall()
                # Convertir sqlite.Row a dict si es necesario
                if self.db_type == 'sqlite':
                    results = [dict(row) if isinstance(row, sqlite3.Row) else row for row in results]
                return results
            else:
                # Para INSERT, UPDATE, DELETE
                return cursor.rowcount
    
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
            
            # Insertar roles por defecto usando try/except para compatibilidad
            try:
                self._cursor_execute(cursor, 
                    "INSERT INTO roles (nombre, descripcion) VALUES (%s, %s)", 
                    ('admin', 'Administrador del sistema'))
                self._cursor_execute(cursor, 
                    "INSERT INTO roles (nombre, descripcion) VALUES (%s, %s)", 
                    ('reclutador', 'Reclutador'))
                self._cursor_execute(cursor, 
                    "INSERT INTO roles (nombre, descripcion) VALUES (%s, %s)", 
                    ('gerente', 'Gerente de RRHH'))
                self._cursor_execute(cursor, 
                    "INSERT INTO roles (nombre, descripcion) VALUES (%s, %s)", 
                    ('candidato', 'Candidato'))
            except (pymysql.err.IntegrityError, sqlite3.IntegrityError):
                # Los roles ya existen, continuar
                pass
            
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
                        telefono VARCHAR(20),
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
                        telefono TEXT,
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
