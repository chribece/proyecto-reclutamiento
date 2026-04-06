import os

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
    
    # Configuración MariaDB
    DB_HOST = os.environ.get('DB_HOST') or 'localhost'
    DB_PORT = int(os.environ.get('DB_PORT') or 3306)
    DB_USER = os.environ.get('DB_USER') or 'root'
    DB_PASSWORD = os.environ.get('DB_PASSWORD') or '123456'  # Contraseña de MariaDB
    DB_NAME = os.environ.get('DB_NAME') or 'reclutamiento'
    
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