#!/usr/bin/env python3
"""
Script para inicializar la base de datos en producción (Render)
Crea las tablas y usuarios de prueba automáticamente de forma idempotente
"""

import os
from database import db
from models import Usuario

def inicializar_produccion():
    """Inicializa la base de datos completa para producción de forma idempotente"""
    
    print("🚀 Inicializando base de datos para producción...")
    
    try:
        # 1. Inicializar la base de datos (ya es idempotente)
        print("📊 Creando tablas de la base de datos...")
        db.init_database()
        print("✅ Tablas verificadas/creadas correctamente")
        
        # 2. Actualizar estructura de forma idempotente
        print("🔧 Verificando estructura de la base de datos...")
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar/agregar campo telefono en candidatos (SQLite/PostgreSQL)
            if db.db_type == 'sqlite':
                cursor.execute('PRAGMA table_info(candidatos)')
                columnas = cursor.fetchall()
                nombres_columnas = [col['name'] for col in columnas]
                
                if 'telefono' not in nombres_columnas:
                    print("➕ Agregando campo 'telefono' a candidatos...")
                    cursor.execute('ALTER TABLE candidatos ADD COLUMN telefono TEXT')
                    print("✅ Campo 'telefono' agregado")
                else:
                    print("✅ Campo 'telefono' ya existe")
            
            elif db.db_type == 'postgresql':
                cursor.execute('''
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'candidatos' AND column_name = 'telefono'
                ''')
                if not cursor.fetchone():
                    print("➕ Agregando campo 'telefono' a candidatos...")
                    cursor.execute('ALTER TABLE candidatos ADD COLUMN telefono TEXT')
                    print("✅ Campo 'telefono' agregado")
                else:
                    print("✅ Campo 'telefono' ya existe")
            
            # Crear tabla sucursales si no existe (idempotente)
            if db.db_type == 'sqlite':
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
                else:
                    print("✅ Tabla 'sucursales' ya existe")
            
            elif db.db_type == 'postgresql':
                cursor.execute('''
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'sucursales'
                    )
                ''')
                if not cursor.fetchone()[0]:
                    print("➕ Creando tabla 'sucursales'...")
                    cursor.execute('''
                        CREATE TABLE sucursales (
                            id_sucursal SERIAL PRIMARY KEY,
                            nombre TEXT NOT NULL,
                            direccion TEXT,
                            telefono TEXT,
                            activa INTEGER DEFAULT 1
                        )
                    ''')
                    cursor.execute('INSERT INTO sucursales (nombre, activa) VALUES (%s, %s)', ('Matriz', 1))
                    print("✅ Tabla 'sucursales' creada")
                else:
                    print("✅ Tabla 'sucursales' ya existe")
            
            # Verificar/agregar campo id_sucursal en cargos
            if db.db_type == 'sqlite':
                cursor.execute('PRAGMA table_info(cargos)')
                columnas_cargos = cursor.fetchall()
                nombres_columnas_cargos = [col['name'] for col in columnas_cargos]
                
                if 'id_sucursal' not in nombres_columnas_cargos:
                    print("➕ Agregando campo 'id_sucursal' a cargos...")
                    cursor.execute('ALTER TABLE cargos ADD COLUMN id_sucursal INTEGER')
                    print("✅ Campo 'id_sucursal' agregado")
                else:
                    print("✅ Campo 'id_sucursal' ya existe")
            
            elif db.db_type == 'postgresql':
                cursor.execute('''
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'cargos' AND column_name = 'id_sucursal'
                ''')
                if not cursor.fetchone():
                    print("➕ Agregando campo 'id_sucursal' a cargos...")
                    cursor.execute('ALTER TABLE cargos ADD COLUMN id_sucursal INTEGER')
                    print("✅ Campo 'id_sucursal' agregado")
                else:
                    print("✅ Campo 'id_sucursal' ya existe")
            
            conn.commit()
        
        # 3. Crear usuarios de prueba de forma idempotente
        print("👥 Verificando usuarios de prueba...")
        crear_usuarios_produccion_idempotente()
        
        print("🎉 ¡Base de datos inicializada exitosamente para producción!")
        return True
        
    except Exception as e:
        print(f"❌ Error al inicializar producción: {str(e)}")
        return False

def crear_usuarios_produccion_idempotente():
    """Crea los usuarios de prueba de forma idempotente (no falla si ya existen)"""
    
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
                print(f"✅ Usuario creado: {usuario_data['email']}")
            else:
                print(f"✅ Usuario ya existe: {usuario_data['email']}")
        except Exception as e:
            print(f"⚠️ Error con usuario {usuario_data['email']}: {str(e)}")
            # No fallar completamente si un usuario falla

if __name__ == "__main__":
    inicializar_produccion()
