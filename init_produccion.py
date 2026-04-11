#!/usr/bin/env python3
"""
Script para inicializar la base de datos en producción (Render)
Crea las tablas y usuarios de prueba automáticamente
"""

import os
from database import db
from models import Usuario

def inicializar_produccion():
    """Inicializa la base de datos completa para producción"""
    
    print("🚀 Inicializando base de datos para producción...")
    
    try:
        # 1. Inicializar la base de datos
        print("📊 Creando tablas de la base de datos...")
        db.init_database()
        print("✅ Tablas creadas correctamente")
        
        # 2. Actualizar estructura (agregar campos faltantes)
        print("🔧 Actualizando estructura de la base de datos...")
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar si la tabla candidatos tiene el campo telefono
            cursor.execute('PRAGMA table_info(candidatos)')
            columnas = cursor.fetchall()
            nombres_columnas = [col['name'] for col in columnas]
            
            if 'telefono' not in nombres_columnas:
                print("➕ Agregando campo 'telefono' a candidatos...")
                cursor.execute('ALTER TABLE candidatos ADD COLUMN telefono TEXT')
                print("✅ Campo 'telefono' agregado")
            
            # Crear tabla sucursales si no existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sucursales'")
            if not cursor.fetchone():
                print("➕ Creando tabla 'sucursales'...")
                cursor.execute('''
                    CREATE TABLE sucursales (
                        id_sucursal INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre TEXT NOT NULL,
                        direccion TEXT,
                        telefono TEXT,
                        activa INTEGER DEFAULT 1
                    )
                ''')
                cursor.execute('INSERT INTO sucursales (nombre, activa) VALUES (?, ?)', ('Matriz', 1))
                print("✅ Tabla 'sucursales' creada")
            
            # Verificar si la tabla cargos tiene el campo id_sucursal
            cursor.execute('PRAGMA table_info(cargos)')
            columnas_cargos = cursor.fetchall()
            nombres_columnas_cargos = [col['name'] for col in columnas_cargos]
            
            if 'id_sucursal' not in nombres_columnas_cargos:
                print("➕ Agregando campo 'id_sucursal' a cargos...")
                cursor.execute('ALTER TABLE cargos ADD COLUMN id_sucursal INTEGER')
                print("✅ Campo 'id_sucursal' agregado")
            
            conn.commit()
        
        # 3. Crear usuarios de prueba
        print("👥 Creando usuarios de prueba...")
        crear_usuarios_produccion()
        
        print("🎉 ¡Base de datos inicializada exitosamente para producción!")
        return True
        
    except Exception as e:
        print(f"❌ Error al inicializar producción: {str(e)}")
        return False

def crear_usuarios_produccion():
    """Crea los usuarios de prueba para producción"""
    
    usuarios = [
        {
            'nombre_usuario': 'admin',
            'email': 'admin@reclutamiento.com',
            'password': 'Admin123!',
            'rol_id': 1  # admin
        },
        {
            'nombre_usuario': 'reclutador1',
            'email': 'reclutador@reclutamiento.com',
            'password': 'Reclu123!',
            'rol_id': 2  # reclutador
        },
        {
            'nombre_usuario': 'gerente1',
            'email': 'gerente@reclutamiento.com',
            'password': 'Gerente123!',
            'rol_id': 3  # gerente
        },
        {
            'nombre_usuario': 'juan.perez',
            'email': 'juan.perez@email.com',
            'password': 'Candidato1!',
            'rol_id': 4  # candidato
        },
        {
            'nombre_usuario': 'maria.garcia',
            'email': 'maria.garcia@email.com',
            'password': 'Candidato2!',
            'rol_id': 4  # candidato
        }
    ]
    
    for usuario_data in usuarios:
        try:
            # Verificar si el usuario ya existe
            usuario_existente = Usuario.get_by_email(usuario_data['email'])
            if not usuario_existente:
                usuario = Usuario(
                    nombre_usuario=usuario_data['nombre_usuario'],
                    email=usuario_data['email'],
                    password=usuario_data['password'],
                    rol_id=usuario_data['rol_id']
                )
                usuario.save()
                print(f"✅ Usuario creado: {usuario_data['email']} ({usuario_data['nombre_usuario']})")
            else:
                print(f"✅ Usuario ya existe: {usuario_data['email']}")
        except Exception as e:
            print(f"❌ Error creando usuario {usuario_data['email']}: {str(e)}")

if __name__ == "__main__":
    inicializar_produccion()
