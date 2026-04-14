"""
Script de migración para agregar columna fecha_actualizacion a postulaciones
Ejecutar en producción: python migrar_postulaciones.py
"""
import os
import psycopg2
from urllib.parse import urlparse

def migrar():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL no configurada")
        return
    
    parsed = urlparse(database_url)
    conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        database=parsed.path[1:],
        user=parsed.username,
        password=parsed.password
    )
    
    cursor = conn.cursor()
    
    # Verificar si la columna existe
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='postulaciones' AND column_name='fecha_actualizacion'
    """)
    
    if cursor.fetchone():
        print("La columna fecha_actualizacion ya existe")
    else:
        print("Agregando columna fecha_actualizacion...")
        cursor.execute("""
            ALTER TABLE postulaciones 
            ADD COLUMN fecha_actualizacion TIMESTAMP
        """)
        conn.commit()
        print("Columna agregada exitosamente")
    
    cursor.close()
    conn.close()

if __name__ == '__main__':
    migrar()
