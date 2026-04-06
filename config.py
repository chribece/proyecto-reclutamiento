import os

# Obtener el directorio base del proyecto
basedir = os.path.abspath(os.path.dirname(__file__))

# Detectar si tenemos credenciales completas de MySQL
mysql_configured = all([
    os.environ.get('DB_HOST'),
    os.environ.get('DB_USER'),
    os.environ.get('DB_PASSWORD'),
    os.environ.get('DB_NAME')
])

# Determinar la URI de la base de datos según la configuración
if mysql_configured and os.environ.get('FLASK_ENV') != 'testing':
    # Usar MySQL
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://"
        f"{os.environ.get('DB_USER')}:"
        f"{os.environ.get('DB_PASSWORD')}@"
        f"{os.environ.get('DB_HOST')}:"
        f"{os.environ.get('DB_PORT', 3306)}/"
        f"{os.environ.get('DB_NAME')}"
    )
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    print(f" Usando MySQL: {os.environ.get('DB_HOST')}")
else:
    # Fallback a SQLite
    # Crear directorio instance si no existe
    instance_dir = os.path.join(basedir, "instance")
    os.makedirs(instance_dir, exist_ok=True)
    
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(instance_dir, "reclutamiento.db")}'
    SQLALCHEMY_ENGINE_OPTIONS = {}
    print(f" Usando SQLite: {os.path.join(instance_dir, 'reclutamiento.db')}")

def get_database_uri():
    """
    Determina la URI de la base de datos basada en las variables de entorno.
    Prioridad: MySQL/PostgreSQL > SQLite (fallback)
    """
    return SQLALCHEMY_DATABASE_URI

def get_mysql_config():
    """Configuración específica para MySQL con soporte SSL"""
    if mysql_configured:
        config = {
            'host': os.environ.get('DB_HOST'),
            'port': int(os.environ.get('DB_PORT') or 3306),
            'user': os.environ.get('DB_USER'),
            'password': os.environ.get('DB_PASSWORD'),
            'database': os.environ.get('DB_NAME'),
            'charset': 'utf8mb4',
            'cursorclass': 'pymysql.cursors.DictCursor',
            'autocommit': False
        }
        
        # Soporte SSL para PlanetScale/AWS
        DB_SSL_CA = os.environ.get('DB_SSL_CA')
        DB_SSL_CERT = os.environ.get('DB_SSL_CERT')
        DB_SSL_KEY = os.environ.get('DB_SSL_KEY')
        DB_SSL_VERIFY = os.environ.get('DB_SSL_VERIFY', 'True').lower() == 'true'
        
        # Agregar configuración SSL si está disponible
        if DB_SSL_CA:
            config.update({
                'ssl': {
                    'ca': DB_SSL_CA,
                    'cert': DB_SSL_CERT,
                    'key': DB_SSL_KEY,
                    'check_hostname': DB_SSL_VERIFY
                }
            })
        
        return config
    else:
        return None  # Usar SQLite

class Config:
    # Seguridad
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-2024-reclutamiento'
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'  # True en producción con HTTPS
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hora
    
    # Configuración del servidor para producción
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    
    # Configuración de Base de Datos con soporte para múltiples entornos
    # Variables de entorno para Render.com
    DB_HOST = os.environ.get('DB_HOST')
    DB_PORT = int(os.environ.get('DB_PORT') or 3306)
    DB_USER = os.environ.get('DB_USER')
    DB_PASSWORD = os.environ.get('DB_PASSWORD')
    DB_NAME = os.environ.get('DB_NAME')
    
    # Soporte SSL para PlanetScale/AWS
    DB_SSL_CA = os.environ.get('DB_SSL_CA')
    DB_SSL_CERT = os.environ.get('DB_SSL_CERT')
    DB_SSL_KEY = os.environ.get('DB_SSL_KEY')
    DB_SSL_VERIFY = os.environ.get('DB_SSL_VERIFY', 'True').lower() == 'true'
    
    # URI de la base de datos para SQLAlchemy (determinada automáticamente)
    SQLALCHEMY_DATABASE_URI = get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Opciones del motor específicas para cada base de datos
    SQLALCHEMY_ENGINE_OPTIONS = globals()['SQLALCHEMY_ENGINE_OPTIONS']
    
    # Colores corporativos para uso en templates
    COLORS = {
        'primary': '#f2a517',      # Amarillo/Dorado
        'secondary': '#ef9120',    # Naranja
        'dark': '#161930',         # Azul oscuro/Navy
        'light': '#dcdde3'         # Gris claro
    }
    
    # Roles disponibles
    ROLES = {
        'admin': 'Administrador',
        'reclutador': 'Reclutador',
        'candidato': 'Candidato',
        'gerente': 'Gerente de RRHH'
    }