#!/usr/bin/env python3
"""
Script para inicializar la base de datos en producción (Render)
Crea las tablas y usuarios de prueba automáticamente de forma idempotente
Soporte completo para PostgreSQL y SQLite
"""

import os
from database import db, get_db_type
from models import Usuario

def _get_count_from_cursor(cursor, table_name):
    """Obtiene el valor COUNT(*) compatible con dict (PostgreSQL) y tuple (SQLite/MySQL)"""
    cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
    row = cursor.fetchone()
    if row is None:
        return 0
    
    # Si es tupla/lista (SQLite/MySQL), usar índice
    if isinstance(row, (tuple, list)):
        return row[0]
    # Si es diccionario (PostgreSQL), usar clave
    else:
        return row.get('count', 0)

def inicializar_produccion():
    """Inicializa la base de datos completa para producción de forma idempotente"""
    
    print(" Inicializando base de datos para producción...")
    
    try:
        # 1. Inicializar la base de datos (ya es idempotente)
        print(" Creando tablas de la base de datos...")
        db.init_database()
        print(" Tablas verificadas/creadas correctamente")
        
        # 2. Verificar estructura (ya está en init_database)
        print(" Verificando estructura de la base de datos...")
        
        # 3. Crear usuarios de prueba de forma idempotente
        print(" Verificando usuarios de prueba...")
        crear_usuarios_produccion_idempotente()
        
        print(" Base de datos inicializada exitosamente para producción!")
        return True
        
    except Exception as e:
        print(f" Error al inicializar producción: {str(e)}")
        return False

def crear_usuarios_produccion_idempotente():
    """Crea los usuarios de prueba de forma idempotente (no falla si ya existen)"""
    
    # Usuarios específicos solicitados
    usuarios = [
        {
            'nombre_usuario': 'admin',
            'email': 'admin@reclutamiento.com',
            'password': 'Admin123!',
            'rol_id': 1,  # admin
            'nombre_completo': 'Administrador'
        },
        {
            'nombre_usuario': 'maria.garcia',
            'email': 'reclutador@empresa.com',
            'password': 'Reclutador123!',
            'rol_id': 2,  # reclutador
            'nombre_completo': 'María García'
        },
        {
            'nombre_usuario': 'carlos.lopez',
            'email': 'reclutador2@empresa.com',
            'password': 'Reclutador123!',
            'rol_id': 2,  # reclutador
            'nombre_completo': 'Carlos López'
        },
        {
            'nombre_usuario': 'juan.perez',
            'email': 'candidato@ejemplo.com',
            'password': 'Candidato123!',
            'rol_id': 4,  # candidato
            'nombre_completo': 'Juan Pérez'
        }
    ]
    
    db_type = get_db_type()
    
    for usuario_data in usuarios:
        try:
            # Verificar si el usuario ya existe
            usuario_existente = Usuario.get_by_email(usuario_data['email'])
            if not usuario_existente:
                # Crear usuario
                usuario = Usuario(
                    nombre_usuario=usuario_data['nombre_usuario'],
                    email=usuario_data['email'],
                    rol_id=usuario_data['rol_id']
                )
                usuario.set_password(usuario_data['password'])
                usuario.save()
                print(f" Usuario creado: {usuario_data['email']} ({usuario_data['nombre_completo']})")
            else:
                print(f" Usuario ya existe: {usuario_data['email']}")
                
        except Exception as e:
            print(f" Error con usuario {usuario_data['email']}: {str(e)}")
            # No fallar completamente si un usuario falla

def verificar_y_crear_datos_iniciales():
    """Verifica y crea datos iniciales necesarios para el funcionamiento"""
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar si hay sucursales
            if _get_count_from_cursor(cursor, 'sucursales') == 0:
                print(" Creando sucursal por defecto...")
                if db.db_type == 'postgresql':
                    cursor.execute("INSERT INTO sucursales (nombre, activa) VALUES (%s, %s)", ('Matriz', 1))
                else:
                    cursor.execute("INSERT INTO sucursales (nombre, activa) VALUES (?, ?)", ('Matriz', 1))
                print(" Sucursal 'Matriz' creada")
            
            # Verificar si hay cargos de ejemplo
            if _get_count_from_cursor(cursor, 'cargos') == 0:
                print(" Creando cargos de ejemplo...")
                cargos_ejemplo = [
                    ('Desarrollador Python', 'Desarrollo de aplicaciones web Python', 'TI', 1500.00, 2500.00, 'Tiempo completo', 1),
                    ('Analista de RRHH', 'Reclutamiento y selección de personal', 'RRHH', 1200.00, 1800.00, 'Tiempo completo', 1),
                    ('Contador', 'Gestión contable y financiera', 'Contabilidad', 1300.00, 2000.00, 'Tiempo completo', 1)
                ]
                
                for cargo in cargos_ejemplo:
                    if db.db_type == 'postgresql':
                        cursor.execute("""
                            INSERT INTO cargos (nombre, descripcion, departamento, salario_minimo, salario_maximo, tipo_contrato, id_sucursal) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, cargo)
                    else:
                        cursor.execute("""
                            INSERT INTO cargos (nombre, descripcion, departamento, salario_minimo, salario_maximo, tipo_contrato, id_sucursal) 
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, cargo)
                
                print(" Cargos de ejemplo creados")
            
            conn.commit()
            
    except Exception as e:
        print(f" Error creando datos iniciales: {str(e)}")

if __name__ == "__main__":
    inicializar_produccion()
    verificar_y_crear_datos_iniciales()
