#!/usr/bin/env python3
"""
Script de inicio para producción en Render
Inicia la aplicación Flask con Gunicorn en el puerto correcto
"""

import os
import sys
import subprocess

def main():
    """Inicia la aplicación con Gunicorn en el puerto de Render"""
    
    # Obtener puerto de Render o usar puerto por defecto
    port = os.environ.get('PORT', '5000')
    
    print(f" Iniciando aplicación en puerto {port}")
    print(f" Environment: {os.environ.get('FLASK_ENV', 'development')}")
    print(f" Database URL: {'Configured' if os.environ.get('DATABASE_URL') else 'Not configured'}")
    
    # Construir comando Gunicorn
    cmd = [
        'gunicorn',
        'app:app',
        '--bind', f'0.0.0.0:{port}',
        '--workers', '2',
        '--timeout', '120',
        '--access-logfile', '-',
        '--error-logfile', '-'
    ]
    
    print(f" Ejecutando: {' '.join(cmd)}")
    
    # Iniciar Gunicorn
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f" Error al iniciar Gunicorn: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print(" Aplicación detenida por el usuario")
        sys.exit(0)

if __name__ == '__main__':
    main()
