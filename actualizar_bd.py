#!/usr/bin/env python3
"""
Script para actualizar la base de datos y agregar campos faltantes
"""

from database import db

def actualizar_base_de_datos():
    """Agrega campos faltantes a las tablas existentes"""
    
    print("🔧 Actualizando estructura de la base de datos...")
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar si la tabla candidatos tiene el campo telefono
            cursor.execute('PRAGMA table_info(candidatos)')
            columnas = cursor.fetchall()
            nombres_columnas = [col['name'] for col in columnas]
            
            print("📋 Columnas actuales en candidatos:", nombres_columnas)
            
            # Agregar campo telefono si no existe
            if 'telefono' not in nombres_columnas:
                print("➕ Agregando campo 'telefono' a la tabla candidatos...")
                if db.db_type == 'mysql':
                    cursor.execute('ALTER TABLE candidatos ADD COLUMN telefono VARCHAR(20)')
                else:
                    cursor.execute('ALTER TABLE candidatos ADD COLUMN telefono TEXT')
                print("✅ Campo 'telefono' agregado correctamente")
            else:
                print("✅ Campo 'telefono' ya existe")
            
            conn.commit()
            print("🎉 ¡Base de datos actualizada exitosamente!")
            
    except Exception as e:
        print(f"❌ Error al actualizar la base de datos: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    actualizar_base_de_datos()
