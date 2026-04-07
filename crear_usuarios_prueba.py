#!/usr/bin/env python3
"""
Script para crear usuarios de prueba en el sistema de reclutamiento
Genera hashes de contraseñas seguros y crea usuarios administrador, reclutador y candidatos
"""

import os
import sys
from werkzeug.security import generate_password_hash
from database import db

def crear_usuarios_prueba():
    """Crea usuarios de prueba con contraseñas seguras"""
    
    # Definir usuarios de prueba
    usuarios_prueba = [
        {
            'nombre_usuario': 'admin',
            'email': 'admin@reclutamiento.com',
            'password': 'Admin123!',
            'rol_id': 1,  # Administrador
            'descripcion': 'Usuario administrador del sistema'
        },
        {
            'nombre_usuario': 'reclutador1',
            'email': 'reclutador@reclutamiento.com',
            'password': 'Reclu123!',
            'rol_id': 2,  # Reclutador
            'descripcion': 'Usuario reclutador de prueba'
        },
        {
            'nombre_usuario': 'gerente1',
            'email': 'gerente@reclutamiento.com',
            'password': 'Gerente123!',
            'rol_id': 3,  # Gerente
            'descripcion': 'Usuario gerente de RRHH'
        }
    ]
    
    print("🔧 Creando usuarios de prueba...")
    print("=" * 50)
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            for usuario in usuarios_prueba:
                # Generar hash de la contraseña
                password_hash = generate_password_hash(usuario['password'], method='pbkdf2:sha256')
                
                # Verificar si el usuario ya existe
                db._cursor_execute(cursor, 'SELECT id_usuario FROM usuarios WHERE email = %s', (usuario['email'],))
                if cursor.fetchone():
                    print(f"⚠️  El usuario {usuario['email']} ya existe. Omitiendo...")
                    continue
                
                # Insertar usuario
                db._cursor_execute(cursor, '''
                    INSERT INTO usuarios (nombre_usuario, email, password_hash, rol_id, activo)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (
                    usuario['nombre_usuario'],
                    usuario['email'],
                    password_hash,
                    usuario['rol_id'],
                    1  # activo
                ))
                
                print(f"✅ Usuario creado: {usuario['nombre_usuario']}")
                print(f"   Email: {usuario['email']}")
                print(f"   Contraseña: {usuario['password']}")
                print(f"   Rol: {usuario['descripcion']}")
                print("-" * 30)
            
            conn.commit()
            print("🎉 ¡Usuarios de prueba creados exitosamente!")
            
    except Exception as e:
        print(f"❌ Error al crear usuarios: {str(e)}")
        return False
    
    return True

def mostrar_credenciales():
    """Muestra las credenciales de los usuarios de prueba"""
    print("\n📋 CREDENCIALES DE PRUEBA")
    print("=" * 50)
    print("🔑 ADMINISTRADOR:")
    print("   Usuario: admin@reclutamiento.com")
    print("   Contraseña: Admin123!")
    print("   Rol: Administrador del sistema")
    print()
    print("👤 RECLUTADOR:")
    print("   Usuario: reclutador@reclutamiento.com")
    print("   Contraseña: Reclu123!")
    print("   Rol: Reclutador")
    print()
    print("👔 GERENTE:")
    print("   Usuario: gerente@reclutamiento.com")
    print("   Contraseña: Gerente123!")
    print("   Rol: Gerente de RRHH")
    print()
    print("🎓 CANDIDATOS (se registran por sí mismos):")
    print("   Los candidatos se registran mediante el formulario público")
    print("   Pueden usar cualquier email y contraseña al registrarse")
    print("=" * 50)

def crear_candidatos_prueba():
    """Crea algunos candidatos de prueba"""
    candidatos_prueba = [
        {
            'cedula': '1234567890',
            'nombre': 'Juan',
            'apellido': 'Pérez',
            'email': 'juan.perez@email.com',
            'telefono': '0991234567',
            'password': 'Candidato1!',
            'resumen': 'Desarrollador Python con 5 años de experiencia',
            'habilidades': ['Python', 'Django', 'JavaScript', 'React'],
            'experiencia_anos': 5,
            'nivel_educativo': 'Universitario',
            'direccion_domicilio': 'Quito, Ecuador',
            'disponibilidad': 'Inmediata',
            'salario_esperado': 20000.0
        },
        {
            'cedula': '0987654321',
            'nombre': 'María',
            'apellido': 'García',
            'email': 'maria.garcia@email.com',
            'telefono': '0998765432',
            'password': 'Candidato2!',
            'resumen': 'Diseñadora UX/UI especializada en interfaces móviles',
            'habilidades': ['Figma', 'Adobe XD', 'Sketch', 'Photoshop'],
            'experiencia_anos': 3,
            'nivel_educativo': 'Universitario',
            'direccion_domicilio': 'Guayaquil, Ecuador',
            'disponibilidad': '2 semanas',
            'salario_esperado': 18000.0
        }
    ]
    
    print("\n👥 Creando candidatos de prueba...")
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            for candidato in candidatos_prueba:
                # Verificar si el candidato ya existe
                db._cursor_execute(cursor, 'SELECT cedula FROM candidatos WHERE cedula = %s', (candidato['cedula'],))
                if cursor.fetchone():
                    print(f"⚠️  El candidato con cédula {candidato['cedula']} ya existe. Omitiendo...")
                    continue
                
                # Crear usuario para el candidato
                password_hash = generate_password_hash(candidato['password'], method='pbkdf2:sha256')
                db._cursor_execute(cursor, '''
                    INSERT INTO usuarios (nombre_usuario, email, password_hash, rol_id, activo)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (
                    candidato['email'].split('@')[0],  # nombre_usuario desde email
                    candidato['email'],
                    password_hash,
                    4,  # rol_id = candidato
                    1  # activo
                ))
                
                # Crear candidato
                import json
                habilidades_json = json.dumps(candidato['habilidades'])
                
                db._cursor_execute(cursor, '''
                    INSERT INTO candidatos (
                        cedula, nombre, apellido, email, resumen,
                        habilidades, experiencia_anos, nivel_educativo, 
                        direccion_domicilio, disponibilidad, salario_esperado, activo
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    candidato['cedula'],
                    candidato['nombre'],
                    candidato['apellido'],
                    candidato['email'],
                    candidato['resumen'],
                    habilidades_json,
                    candidato['experiencia_anos'],
                    candidato['nivel_educativo'],
                    candidato['direccion_domicilio'],
                    candidato['disponibilidad'],
                    candidato['salario_esperado'],
                    1  # activo
                ))
                
                print(f"✅ Candidato creado: {candidato['nombre']} {candidato['apellido']}")
                print(f"   Email: {candidato['email']}")
                print(f"   Contraseña: {candidato['password']}")
                print(f"   Cédula: {candidato['cedula']}")
                print("-" * 30)
            
            conn.commit()
            print("🎉 ¡Candidatos de prueba creados exitosamente!")
            
    except Exception as e:
        print(f"❌ Error al crear candidatos: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Inicializando usuarios de prueba para el Sistema de Reclutamiento")
    print("=" * 70)
    
    # Inicializar la base de datos primero
    try:
        db.init_database()
        print("✅ Base de datos inicializada")
    except Exception as e:
        print(f"❌ Error al inicializar la base de datos: {str(e)}")
        sys.exit(1)
    
    # Crear usuarios de prueba
    if crear_usuarios_prueba():
        # Crear candidatos de prueba
        crear_candidatos_prueba()
        
        # Mostrar credenciales
        mostrar_credenciales()
        
        print("\n🎯 INSTRUCCIONES:")
        print("1. Inicia sesión con los usuarios de prueba según el rol que necesites")
        print("2. Los candidatos pueden registrarse usando el formulario público")
        print("3. Las contraseñas son seguras y están hasheadas con PBKDF2")
        print("4. Puedes modificar las contraseñas en este script si es necesario")
        print("\n🚀 ¡Listo para pruebas!")
    else:
        print("❌ No se pudieron crear los usuarios de prueba")
        sys.exit(1)
