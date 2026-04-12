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
    
    def _create_table_sql(self, table_name: str, columns: list) -> str:
        """Genera SQL CREATE TABLE según el tipo de base de datos"""
        if self.db_type == 'postgresql':
            id_column = "SERIAL PRIMARY KEY"
            timestamp_default = "DEFAULT NOW()"
            boolean_default = "DEFAULT TRUE"
        else:
            id_column = "INTEGER PRIMARY KEY AUTOINCREMENT"
            timestamp_default = "DEFAULT CURRENT_TIMESTAMP"
            boolean_default = "DEFAULT 1"
        
        columns_sql = []
        for col in columns:
            if col['name'].endswith('_id') and self.db_type == 'postgresql' and 'id_' not in col['name']:
                columns_sql.append(f"{col['name']} {id_column}")
            else:
                default_clause = f" {col['default']}" if col.get('default') else ""
                columns_sql.append(f"{col['name']} {col['type']}{default_clause}")
        
        return f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                {', '.join(columns_sql)}
            )
        """
    
    def init_database(self):
        """Inicializa la base de datos con sintaxis correcta para cada tipo"""
        print(f"🔧 Inicializando base de datos: {self.db_type}")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabla roles
            roles_sql = self._create_table_sql('roles', [
                {'name': 'id_rol', 'type': 'INTEGER PRIMARY KEY' if self.db_type != 'postgresql' else 'SERIAL PRIMARY KEY'},
                {'name': 'nombre', 'type': 'VARCHAR(50) NOT NULL'},
                {'name': 'descripcion', 'type': 'TEXT'}
            ])
            cursor.execute(roles_sql)
            
            # Insertar roles por defecto
            cursor.execute("SELECT COUNT(*) FROM roles")
            if cursor.fetchone()[0] == 0:
                roles_data = [
                    (1, 'admin', 'Administrador del sistema'),
                    (2, 'reclutador', 'Reclutador de personal'),
                    (3, 'gerente', 'Gerente de RRHH'),
                    (4, 'candidato', 'Candidato a puesto')
                ]
                if self.db_type == 'postgresql':
                    cursor.executemany("INSERT INTO roles (id_rol, nombre, descripcion) VALUES (%s, %s, %s)", roles_data)
                else:
                    cursor.executemany("INSERT INTO roles (id_rol, nombre, descripcion) VALUES (?, ?, ?)", roles_data)
            
            # Tabla usuarios
            usuarios_sql = self._create_table_sql('usuarios', [
                {'name': 'id_usuario', 'type': 'INTEGER PRIMARY KEY' if self.db_type != 'postgresql' else 'SERIAL PRIMARY KEY'},
                {'name': 'nombre_usuario', 'type': 'VARCHAR(50) NOT NULL'},
                {'name': 'email', 'type': 'VARCHAR(100) UNIQUE NOT NULL'},
                {'name': 'password_hash', 'type': 'VARCHAR(255) NOT NULL'},
                {'name': 'rol_id', 'type': 'INTEGER NOT NULL'},
                {'name': 'activo', 'type': f'INTEGER {boolean_default}'},
                {'name': 'created_at', 'type': f'TIMESTAMP {timestamp_default}'},
                {'name': 'ultimo_acceso', 'type': 'TIMESTAMP NULL'}
            ])
            cursor.execute(usuarios_sql)
            
            # Tabla sucursales
            sucursales_sql = self._create_table_sql('sucursales', [
                {'name': 'id_sucursal', 'type': 'INTEGER PRIMARY KEY' if self.db_type != 'postgresql' else 'SERIAL PRIMARY KEY'},
                {'name': 'nombre', 'type': 'VARCHAR(100) NOT NULL'},
                {'name': 'direccion', 'type': 'TEXT'},
                {'name': 'telefono', 'type': 'VARCHAR(20)'},
                {'name': 'activa', 'type': f'INTEGER {boolean_default}'}
            ])
            cursor.execute(sucursales_sql)
            
            # Insertar sucursal por defecto
            cursor.execute("SELECT COUNT(*) FROM sucursales")
            if cursor.fetchone()[0] == 0:
                if self.db_type == 'postgresql':
                    cursor.execute("INSERT INTO sucursales (nombre, activa) VALUES (%s, %s)", ('Matriz', 1))
                else:
                    cursor.execute("INSERT INTO sucursales (nombre, activa) VALUES (?, ?)", ('Matriz', 1))
            
            # Tabla cargos
            cargos_sql = self._create_table_sql('cargos', [
                {'name': 'id_cargo', 'type': 'INTEGER PRIMARY KEY' if self.db_type != 'postgresql' else 'SERIAL PRIMARY KEY'},
                {'name': 'nombre', 'type': 'VARCHAR(100) NOT NULL'},
                {'name': 'descripcion', 'type': 'TEXT'},
                {'name': 'departamento', 'type': 'VARCHAR(50) NOT NULL'},
                {'name': 'salario_minimo', 'type': 'DECIMAL(10,2)'},
                {'name': 'salario_maximo', 'type': 'DECIMAL(10,2)'},
                {'name': 'tipo_contrato', 'type': "VARCHAR(50) DEFAULT 'Tiempo completo'"},
                {'name': 'id_sucursal', 'type': 'INTEGER'},
                {'name': 'direccion_domicilio', 'type': 'VARCHAR(100)'},
                {'name': 'estado', 'type': "VARCHAR(20) DEFAULT 'Activo'"},
                {'name': 'fecha_creacion', 'type': f'TIMESTAMP {timestamp_default}'},
                {'name': 'fecha_cierre', 'type': 'DATE'}
            ])
            cursor.execute(cargos_sql)
            
            # Tabla candidatos
            candidatos_sql = self._create_table_sql('candidatos', [
                {'name': 'cedula', 'type': 'VARCHAR(10) PRIMARY KEY'},
                {'name': 'nombre', 'type': 'VARCHAR(100) NOT NULL'},
                {'name': 'apellido', 'type': 'VARCHAR(100) NOT NULL'},
                {'name': 'email', 'type': 'VARCHAR(100) UNIQUE NOT NULL'},
                {'name': 'telefono', 'type': 'VARCHAR(20)'},
                {'name': 'resumen', 'type': 'TEXT'},
                {'name': 'habilidades', 'type': 'TEXT'},
                {'name': 'experiencia_anos', 'type': 'INT DEFAULT 0'},
                {'name': 'nivel_educativo', 'type': 'VARCHAR(100)'},
                {'name': 'direccion_domicilio', 'type': 'VARCHAR(100)'},
                {'name': 'disponibilidad', 'type': 'VARCHAR(50)'},
                {'name': 'salario_esperado', 'type': 'DECIMAL(10,2)'},
                {'name': 'fecha_registro', 'type': f'TIMESTAMP {timestamp_default}'},
                {'name': 'activo', 'type': f'INTEGER {boolean_default}'}
            ])
            cursor.execute(candidatos_sql)
            
            # Tabla postulaciones
            postulaciones_sql = self._create_table_sql('postulaciones', [
                {'name': 'id_postulacion', 'type': 'INTEGER PRIMARY KEY' if self.db_type != 'postgresql' else 'SERIAL PRIMARY KEY'},
                {'name': 'cedula', 'type': 'VARCHAR(10) NOT NULL'},
                {'name': 'id_cargo', 'type': 'INTEGER NOT NULL'},
                {'name': 'estado', 'type': "VARCHAR(20) DEFAULT 'Recibido'"},
                {'name': 'fecha_postulacion', 'type': f'TIMESTAMP {timestamp_default}'},
                {'name': 'fuente_reclutamiento', 'type': 'VARCHAR(50)'},
                {'name': 'notas', 'type': 'TEXT'},
                {'name': 'puntaje_evaluacion', 'type': 'INT'}
            ])
            cursor.execute(postulaciones_sql)
            
            # Tabla referencias_personales
            referencias_sql = self._create_table_sql('referencias_personales', [
                {'name': 'id_referencia', 'type': 'INTEGER PRIMARY KEY' if self.db_type != 'postgresql' else 'SERIAL PRIMARY KEY'},
                {'name': 'cedula', 'type': 'VARCHAR(10) NOT NULL'},
                {'name': 'nombre', 'type': 'VARCHAR(100) NOT NULL'},
                {'name': 'telefono', 'type': 'VARCHAR(20)'},
                {'name': 'relacion', 'type': 'VARCHAR(50)'},
                {'name': 'descripcion', 'type': 'VARCHAR(200)'},
                {'name': 'fecha_registro', 'type': f'TIMESTAMP {timestamp_default}'}
            ])
            cursor.execute(referencias_sql)
            
            # Tabla experiencias
            experiencias_sql = self._create_table_sql('experiencias', [
                {'name': 'id_experiencia', 'type': 'INTEGER PRIMARY KEY' if self.db_type != 'postgresql' else 'SERIAL PRIMARY KEY'},
                {'name': 'cedula', 'type': 'VARCHAR(10) NOT NULL'},
                {'name': 'empresa', 'type': 'VARCHAR(100) NOT NULL'},
                {'name': 'cargo', 'type': 'VARCHAR(100) NOT NULL'},
                {'name': 'fecha_inicio', 'type': 'DATE NOT NULL'},
                {'name': 'fecha_fin', 'type': 'DATE'},
                {'name': 'actual', 'type': f'INTEGER DEFAULT 0'},
                {'name': 'descripcion', 'type': 'TEXT'}
            ])
            cursor.execute(experiencias_sql)
            
            # Tabla documentos
            documentos_sql = self._create_table_sql('documentos', [
                {'name': 'id_documento', 'type': 'INTEGER PRIMARY KEY' if self.db_type != 'postgresql' else 'SERIAL PRIMARY KEY'},
                {'name': 'id_postulacion', 'type': 'INTEGER NOT NULL'},
                {'name': 'tipo_documento', 'type': 'VARCHAR(50) NOT NULL'},
                {'name': 'nombre_archivo', 'type': 'VARCHAR(255) NOT NULL'},
                {'name': 'ruta_archivo', 'type': 'VARCHAR(500) NOT NULL'},
                {'name': 'fecha_subida', 'type': f'TIMESTAMP {timestamp_default}'},
                {'name': 'tamano_archivo', 'type': 'INTEGER'}
            ])
            cursor.execute(documentos_sql)
            
            # Tabla estudios
            estudios_sql = self._create_table_sql('estudios', [
                {'name': 'id_estudio', 'type': 'INTEGER PRIMARY KEY' if self.db_type != 'postgresql' else 'SERIAL PRIMARY KEY'},
                {'name': 'nivel_estudio', 'type': 'VARCHAR(100) NOT NULL UNIQUE'}
            ])
            cursor.execute(estudios_sql)
            
            # Insertar niveles educativos
            cursor.execute("SELECT COUNT(*) FROM estudios")
            if cursor.fetchone()[0] == 0:
                niveles_data = [
                    ('Bachiller',),
                    ('Técnico',),
                    ('Universitario',),
                    ('Posgrado',),
                    ('Doctorado',)
                ]
                if self.db_type == 'postgresql':
                    cursor.executemany("INSERT INTO estudios (nivel_estudio) VALUES (%s)", niveles_data)
                else:
                    cursor.executemany("INSERT INTO estudios (nivel_estudio) VALUES (?)", niveles_data)
            
            conn.commit()
            print("✅ Base de datos inicializada correctamente")

# Singleton instance
db = DatabaseManager()
