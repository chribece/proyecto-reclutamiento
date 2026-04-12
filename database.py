import pymysql
import sqlite3
import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from config import Config, get_mysql_config
from datetime import datetime
import os

def get_db_type():
    """Detecta automáticamente el tipo de base de datos"""
    database_url = os.environ.get('DATABASE_URL', '')
    if 'postgresql://' in database_url:
        return 'postgresql'
    elif get_mysql_config():
        return 'mysql'
    else:
        return 'sqlite'

def get_connection_string():
    """Obtiene la cadena de conexión según el tipo de BD"""
    db_type = get_db_type()
    
    if db_type == 'postgresql':
        return os.environ.get('DATABASE_URL')
    elif db_type == 'mysql':
        config = get_mysql_config()
        return f"mysql+pymysql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
    else:
        # SQLite
        instance_dir = os.path.abspath(os.path.dirname(__file__))
        db_path = os.path.join(instance_dir, "instance", "reclutamiento.db")
        return f'sqlite:///{db_path}'

class UniversalCursor:
    """
    Cursor wrapper universal para MySQL, PostgreSQL y SQLite
    Traduce placeholders y convierte resultados a diccionarios
    """
    def __init__(self, cursor, db_type):
        self.cursor = cursor
        self.db_type = db_type
    
    def _convert_query(self, query):
        """Convierte placeholders según el tipo de base de datos"""
        if self.db_type == 'sqlite':
            # SQLite usa ?
            import re
            query = re.sub(r'(?<!\\)%s', '?', query)
        # PostgreSQL y MySQL usan %s
        return query
    
    def _convert_result(self, result):
        """Convierte resultados a diccionarios para compatibilidad universal"""
        if self.db_type == 'sqlite' and hasattr(result, 'keys'):
            # sqlite3.Row a dict
            return dict(result)
        elif self.db_type == 'postgresql' and hasattr(result, 'keys'):
            # psycopg2.extras.RealDictRow ya es como dict
            return dict(result)
        return result
    
    def execute(self, query, params=None):
        """Ejecuta consulta con traducción automática de placeholders"""
        converted_query = self._convert_query(query)
        if params:
            return self.cursor.execute(converted_query, params)
        else:
            return self.cursor.execute(converted_query)
    
    def executemany(self, query, params=None):
        """Ejecuta consultas múltiples con traducción automática"""
        converted_query = self._convert_query(query)
        if params:
            return self.cursor.executemany(converted_query, params)
        else:
            return self.cursor.executemany(converted_query)
    
    def fetchone(self):
        """Convierte resultado a diccionario si es necesario"""
        result = self.cursor.fetchone()
        return self._convert_result(result)
    
    def fetchall(self):
        """Convierte todos los resultados a diccionarios si es necesario"""
        results = self.cursor.fetchall()
        if self.db_type in ['sqlite', 'postgresql']:
            return [self._convert_result(row) for row in results]
        return results
    
    def fetchmany(self, size=None):
        """Convierte múltiples resultados a diccionarios si es necesario"""
        results = self.cursor.fetchmany(size) if size else self.cursor.fetchmany()
        if self.db_type in ['sqlite', 'postgresql']:
            return [self._convert_result(row) for row in results]
        return results
    
    def __getattr__(self, name):
        """Delega todos los demás métodos al cursor original"""
        return getattr(self.cursor, name)

class UniversalConnection:
    """Wrapper universal para conexiones de base de datos"""
    def __init__(self, connection, db_type):
        self.connection = connection
        self.db_type = db_type
    
    def cursor(self):
        """Devuelve cursor universal con traducción automática"""
        if self.db_type == 'postgresql':
            # PostgreSQL con cursor de diccionarios
            original_cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        elif self.db_type == 'mysql':
            # MySQL con DictCursor
            original_cursor = self.connection.cursor()
        else:
            # SQLite con row_factory
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
        
        self.db_type = get_db_type()
        self.connection_string = get_connection_string()
        self.mysql_config = get_mysql_config()
        self.use_mysql = self.mysql_config is not None
        self.use_postgresql = self.db_type == 'postgresql'
        
        self._initialized = True
    
    @contextmanager
    def get_connection(self):
        """Obtiene conexión universal para cualquier base de datos"""
        conn = None
        try:
            if self.use_postgresql:
                # PostgreSQL
                conn = psycopg2.connect(self.connection_string)
            elif self.use_mysql:
                # MySQL con DictCursor
                conn = pymysql.connect(
                    cursorclass=pymysql.cursors.DictCursor,
                    **self.mysql_config
                )
            else:
                # SQLite con row_factory
                db_path = self.connection_string.replace('sqlite:///', '')
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
            
            # Envolver con conexión universal
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
    
    def ejecutar_consulta(self, query: str, params=None, fetch_one=False, fetch_all=False):
        """Método universal para ejecutar consultas"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            if fetch_one:
                return cursor.fetchone()
            elif fetch_all:
                return cursor.fetchall()
            else:
                return cursor.lastrowid if hasattr(cursor, 'lastrowid') else None
    
    def init_database(self):
        """Inicializa la base de datos con sintaxis correcta para cada tipo"""
        print(f" Inicializando base de datos: {self.db_type}")
        
        def get_count(cursor):
            """Función helper para obtener COUNT(*) compatible con dict (PostgreSQL) y tuple (SQLite/MySQL)"""
            row = cursor.fetchone()
            if row is None:
                return 0
            
            # Si es diccionario (PostgreSQL RealDictCursor)
            if isinstance(row, dict):
                # Buscar 'count' primero, luego 'COUNT(*)', luego cualquier valor
                if 'count' in row:
                    return row['count']
                elif 'COUNT(*)' in row:
                    return row['COUNT(*)']
                else:
                    # Retornar el primer valor disponible
                    return next(iter(row.values()), 0)
            # Si es tupla/lista (SQLite/MySQL)
            elif isinstance(row, (tuple, list)):
                return row[0] if len(row) > 0 else 0
            # Caso por defecto
            else:
                return 0
        
        # Variables locales según tipo de BD
        is_postgres = self.db_type == 'postgresql'
        id_type = "SERIAL PRIMARY KEY" if is_postgres else "INTEGER PRIMARY KEY AUTOINCREMENT"
        bool_type = "BOOLEAN" if is_postgres else "INTEGER"
        bool_true = "TRUE" if is_postgres else "1"
        timestamp_now = "NOW()" if is_postgres else "CURRENT_TIMESTAMP"
        placeholder = "%s" if is_postgres else "?"
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabla roles
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS roles (
                    id_rol {id_type},
                    nombre VARCHAR(50) NOT NULL,
                    descripcion TEXT
                )
            """)
            
            # Insertar roles por defecto
            cursor.execute("SELECT COUNT(*) as count FROM roles")
            if get_count(cursor) == 0:
                roles_data = [
                    (1, 'admin', 'Administrador del sistema'),
                    (2, 'reclutador', 'Reclutador de personal'),
                    (3, 'gerente', 'Gerente de RRHH'),
                    (4, 'candidato', 'Candidato a puesto')
                ]
                if is_postgres:
                    cursor.executemany("INSERT INTO roles (id_rol, nombre, descripcion) VALUES (%s, %s, %s)", roles_data)
                else:
                    cursor.executemany("INSERT INTO roles (id_rol, nombre, descripcion) VALUES (?, ?, ?)", roles_data)
            
            # Tabla usuarios
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id_usuario {id_type},
                    nombre_usuario VARCHAR(50) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    rol_id INTEGER NOT NULL,
                    activo {bool_type} DEFAULT {bool_true},
                    created_at TIMESTAMP DEFAULT {timestamp_now},
                    ultimo_acceso TIMESTAMP NULL
                )
            """)
            
            # Tabla sucursales
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS sucursales (
                    id_sucursal {id_type},
                    nombre VARCHAR(100) NOT NULL,
                    direccion TEXT,
                    telefono VARCHAR(20),
                    activa {bool_type} DEFAULT {bool_true}
                )
            """)
            
            # Insertar sucursal por defecto
            cursor.execute("SELECT COUNT(*) as count FROM sucursales")
            if get_count(cursor) == 0:
                if is_postgres:
                    cursor.execute("INSERT INTO sucursales (nombre, activa) VALUES (%s, %s)", ('Matriz', True))
                else:
                    cursor.execute("INSERT INTO sucursales (nombre, activa) VALUES (?, ?)", ('Matriz', 1))
            
            # Tabla cargos
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS cargos (
                    id_cargo {id_type},
                    nombre VARCHAR(100) NOT NULL,
                    descripcion TEXT,
                    departamento VARCHAR(50) NOT NULL,
                    salario_minimo DECIMAL(10,2),
                    salario_maximo DECIMAL(10,2),
                    tipo_contrato VARCHAR(50) DEFAULT 'Tiempo completo',
                    id_sucursal INTEGER,
                    direccion_domicilio VARCHAR(100),
                    estado VARCHAR(20) DEFAULT 'Activo',
                    fecha_creacion TIMESTAMP DEFAULT {timestamp_now},
                    fecha_cierre DATE
                )
            """)
            
            # Tabla candidatos
            cursor.execute(f"""
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
                    fecha_registro TIMESTAMP DEFAULT {timestamp_now},
                    activo {bool_type} DEFAULT {bool_true}
                )
            """)
            
            # Tabla postulaciones
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS postulaciones (
                    id_postulacion {id_type},
                    cedula VARCHAR(10) NOT NULL,
                    id_cargo INTEGER NOT NULL,
                    estado VARCHAR(20) DEFAULT 'Recibido',
                    fecha_postulacion TIMESTAMP DEFAULT {timestamp_now},
                    fuente_reclutamiento VARCHAR(50),
                    notas TEXT,
                    puntaje_evaluacion INT
                )
            """)
            
            # Tabla referencias_personales
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS referencias_personales (
                    id_referencia {id_type},
                    cedula VARCHAR(10) NOT NULL,
                    nombre VARCHAR(100) NOT NULL,
                    telefono VARCHAR(20),
                    relacion VARCHAR(50),
                    descripcion VARCHAR(200),
                    fecha_registro TIMESTAMP DEFAULT {timestamp_now}
                )
            """)
            
            # Tabla experiencias
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS experiencias (
                    id_experiencia {id_type},
                    cedula VARCHAR(10) NOT NULL,
                    empresa VARCHAR(100) NOT NULL,
                    cargo VARCHAR(100) NOT NULL,
                    fecha_inicio DATE NOT NULL,
                    fecha_fin DATE,
                    actual {bool_type} DEFAULT 0,
                    descripcion TEXT
                )
            """)
            
            # Tabla documentos
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS documentos (
                    id_documento {id_type},
                    id_postulacion INTEGER NOT NULL,
                    tipo_documento VARCHAR(50) NOT NULL,
                    nombre_archivo VARCHAR(255) NOT NULL,
                    ruta_archivo VARCHAR(500) NOT NULL,
                    fecha_subida TIMESTAMP DEFAULT {timestamp_now},
                    tamano_archivo INTEGER
                )
            """)
            
            # Tabla estudios
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS estudios (
                    id_estudio {id_type},
                    nivel_estudio VARCHAR(100) NOT NULL UNIQUE
                )
            """)
            
            # Insertar niveles educativos
            cursor.execute("SELECT COUNT(*) as count FROM estudios")
            if get_count(cursor) == 0:
                niveles_data = [
                    ('Bachiller',),
                    ('Técnico',),
                    ('Universitario',),
                    ('Posgrado',),
                    ('Doctorado',)
                ]
                if is_postgres:
                    cursor.executemany("INSERT INTO estudios (nivel_estudio) VALUES (%s)", niveles_data)
                else:
                    cursor.executemany("INSERT INTO estudios (nivel_estudio) VALUES (?)", niveles_data)
            
            conn.commit()
            print(" Base de datos inicializada correctamente")

# Singleton instance
db = DatabaseManager()
