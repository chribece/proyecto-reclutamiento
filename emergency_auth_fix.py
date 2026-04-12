#!/usr/bin/env python3
"""
Fix de emergencia para autenticación
"""

import os
import sys
from werkzeug.security import generate_password_hash

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import db, get_db_type

def emergency_auth_fix():
    """Fix de emergencia para autenticación"""
    print("🚨 FIX DE EMERGENCIA PARA AUTENTICACIÓN")
    print("=" * 50)
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Verificar si existen usuarios
            print("1. 🔍 Verificando usuarios existentes:")
            cursor.execute("SELECT COUNT(*) as count FROM usuarios")
            count = cursor.fetchone()
            user_count = count['count'] if isinstance(count, dict) else count[0]
            print(f"   - Usuarios existentes: {user_count}")
            
            # 2. Verificar si existen roles
            print("2. 🎭 Verificando roles:")
            cursor.execute("SELECT COUNT(*) as count FROM roles")
            role_count = cursor.fetchone()
            role_count = role_count['count'] if isinstance(role_count, dict) else role_count[0]
            print(f"   - Roles existentes: {role_count}")
            
            if role_count == 0:
                print("   📝 Creando roles básicos...")
                if get_db_type() == 'postgresql':
                    cursor.executemany("""
                        INSERT INTO roles (id_rol, nombre) VALUES (%s, %s)
                    """, [
                        (1, 'admin'),
                        (2, 'gerente'),
                        (3, 'reclutador'),
                        (4, 'candidato')
                    ])
                else:
                    cursor.executemany("""
                        INSERT INTO roles (id_rol, nombre) VALUES (?, ?)
                    """, [
                        (1, 'admin'),
                        (2, 'gerente'),
                        (3, 'reclutador'),
                        (4, 'candidato')
                    ])
                print("   ✅ Roles creados")
            
            # 3. Crear/verificar usuarios
            print("3. 👤 Creando/verificando usuarios:")
            
            # Usuario admin
            print("   - Verificando admin...")
            cursor.execute("SELECT id_usuario FROM usuarios WHERE email = %s", ('admin@reclutamiento.com',))
            admin_exists = cursor.fetchone()
            
            if not admin_exists:
                print("     📝 Creando usuario admin...")
                password_hash = generate_password_hash('Admin123!', method='pbkdf2:sha256')
                
                if get_db_type() == 'postgresql':
                    cursor.execute("""
                        INSERT INTO usuarios (nombre_usuario, email, password_hash, rol_id, activo)
                        VALUES (%s, %s, %s, %s, %s)
                    """, ('admin', 'admin@reclutamiento.com', password_hash, 1, True))
                else:
                    cursor.execute("""
                        INSERT INTO usuarios (nombre_usuario, email, password_hash, rol_id, activo)
                        VALUES (?, ?, ?, ?, ?)
                    """, ('admin', 'admin@reclutamiento.com', password_hash, 1, 1))
                print("     ✅ Admin creado")
            else:
                print("     ✅ Admin ya existe")
            
            # Usuario reclutador
            print("   - Verificando reclutador...")
            cursor.execute("SELECT id_usuario FROM usuarios WHERE email = %s", ('reclutador@empresa.com',))
            reclutador_exists = cursor.fetchone()
            
            if not reclutador_exists:
                print("     📝 Creando usuario reclutador...")
                password_hash = generate_password_hash('Reclutador123!', method='pbkdf2:sha256')
                
                if get_db_type() == 'postgresql':
                    cursor.execute("""
                        INSERT INTO usuarios (nombre_usuario, email, password_hash, rol_id, activo)
                        VALUES (%s, %s, %s, %s, %s)
                    """, ('reclutador', 'reclutador@empresa.com', password_hash, 3, True))
                else:
                    cursor.execute("""
                        INSERT INTO usuarios (nombre_usuario, email, password_hash, rol_id, activo)
                        VALUES (?, ?, ?, ?, ?)
                    """, ('reclutador', 'reclutador@empresa.com', password_hash, 3, 1))
                print("     ✅ Reclutador creado")
            else:
                print("     ✅ Reclutador ya existe")
            
            # Usuario reclutador2
            print("   - Verificando reclutador2...")
            cursor.execute("SELECT id_usuario FROM usuarios WHERE email = %s", ('reclutador2@empresa.com',))
            reclutador2_exists = cursor.fetchone()
            
            if not reclutador2_exists:
                print("     📝 Creando usuario reclutador2...")
                password_hash = generate_password_hash('Reclutador123!', method='pbkdf2:sha256')
                
                if get_db_type() == 'postgresql':
                    cursor.execute("""
                        INSERT INTO usuarios (nombre_usuario, email, password_hash, rol_id, activo)
                        VALUES (%s, %s, %s, %s, %s)
                    """, ('reclutador2', 'reclutador2@empresa.com', password_hash, 3, True))
                else:
                    cursor.execute("""
                        INSERT INTO usuarios (nombre_usuario, email, password_hash, rol_id, activo)
                        VALUES (?, ?, ?, ?, ?)
                    """, ('reclutador2', 'reclutador2@empresa.com', password_hash, 3, 1))
                print("     ✅ Reclutador2 creado")
            else:
                print("     ✅ Reclutador2 ya existe")
            
            # 4. Verificar usuarios creados
            print("4. ✅ Verificando usuarios finales:")
            cursor.execute("""
                SELECT u.nombre_usuario, u.email, u.activo, r.nombre as rol_nombre
                FROM usuarios u
                LEFT JOIN roles r ON u.rol_id = r.id_rol
                WHERE u.email IN (%s, %s, %s)
                ORDER BY u.id_usuario
            """, ('admin@reclutamiento.com', 'reclutador@empresa.com', 'reclutador2@empresa.com'))
            
            usuarios = cursor.fetchall()
            for usuario in usuarios:
                if isinstance(usuario, (tuple, list)):
                    nombre, email, activo, rol = usuario
                else:
                    nombre = usuario.get('nombre_usuario')
                    email = usuario.get('email')
                    activo = usuario.get('activo')
                    rol = usuario.get('rol_nombre')
                
                print(f"   - {nombre} ({email}): Activo={activo}, Rol={rol}")
            
            conn.commit()
            print("\n✅ Fix de autenticación completado exitosamente!")
            print("\n🔑 Credenciales para probar:")
            print("   Admin:")
            print("     Email: admin@reclutamiento.com")
            print("     Contraseña: Admin123!")
            print("   Reclutador:")
            print("     Email: reclutador@empresa.com")
            print("     Contraseña: Reclutador123!")
            print("   Reclutador2:")
            print("     Email: reclutador2@empresa.com")
            print("     Contraseña: Reclutador123!")
            
    except Exception as e:
        print(f"❌ Error en fix de autenticación: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    emergency_auth_fix()
