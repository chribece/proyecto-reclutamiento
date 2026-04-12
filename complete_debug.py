#!/usr/bin/env python3
"""
Diagnóstico completo del sistema de reclutamiento
"""

import os
import sys
from database import db, get_db_type
from models import Usuario

def debug_system():
    """Diagnóstico completo del sistema"""
    print("🔍 DIAGNÓSTICO COMPLETO DEL SISTEMA")
    print("=" * 60)
    
    # 1. Verificar conexión básica
    print("1. 🔌 Conexión a la base de datos:")
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 as test, NOW() as tiempo")
            result = cursor.fetchone()
            print(f"   ✅ Conexión OK: {result}")
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")
        return False
    
    # 2. Verificar tipo de base de datos
    print(f"2. 🗄️ Tipo de base de datos: {get_db_type()}")
    
    # 3. Verificar tablas existentes
    print("3. 📋 Tablas en la base de datos:")
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            if get_db_type() == 'postgresql':
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
            else:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            
            tablas = cursor.fetchall()
            for tabla in tablas:
                nombre = tabla[0] if isinstance(tabla, (tuple, list)) else tabla.get('table_name')
                print(f"   - {nombre}")
    except Exception as e:
        print(f"   ❌ Error listando tablas: {e}")
    
    # 4. Verificar estructura de tabla usuarios
    print("4. 👥 Estructura de tabla usuarios:")
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            if get_db_type() == 'postgresql':
                cursor.execute("""
                    SELECT column_name, data_type, column_default, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = 'usuarios'
                    ORDER BY ordinal_position
                """)
            else:
                cursor.execute("PRAGMA table_info(usuarios)")
            
            columnas = cursor.fetchall()
            for col in columnas:
                if isinstance(col, (tuple, list)):
                    print(f"   - {col[0]}: {col[1]} (default: {col[2]}, nullable: {col[3]})")
                else:
                    print(f"   - {col.get('column_name')}: {col.get('data_type')} (default: {col.get('column_default')}, nullable: {col.get('is_nullable')})")
    except Exception as e:
        print(f"   ❌ Error verificando estructura: {e}")
    
    # 5. Verificar usuarios existentes
    print("5. 👤 Usuarios existentes:")
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id_usuario, u.nombre_usuario, u.email, u.activo, u.rol_id, r.nombre as rol_nombre
                FROM usuarios u
                LEFT JOIN roles r ON u.rol_id = r.id_rol
                ORDER BY u.id_usuario
            """)
            usuarios = cursor.fetchall()
            
            if not usuarios:
                print("   ❌ No hay usuarios en la base de datos")
            else:
                for usuario in usuarios:
                    if isinstance(usuario, (tuple, list)):
                        id_u, nombre, email, activo, rol_id, rol_nombre = usuario
                    else:
                        id_u = usuario.get('id_usuario')
                        nombre = usuario.get('nombre_usuario')
                        email = usuario.get('email')
                        activo = usuario.get('activo')
                        rol_id = usuario.get('rol_id')
                        rol_nombre = usuario.get('rol_nombre')
                    
                    print(f"   - ID: {id_u}, Nombre: {nombre}, Email: {email}, Activo: {activo} ({type(activo)}), Rol: {rol_nombre}")
    except Exception as e:
        print(f"   ❌ Error listando usuarios: {e}")
        import traceback
        traceback.print_exc()
    
    # 6. Probar login con admin
    print("6. 🔐 Probando login admin:")
    try:
        admin_user = Usuario.get_by_email_or_username('admin@reclutamiento.com')
        if admin_user:
            print(f"   ✅ Usuario encontrado: {admin_user.nombre_usuario}")
            print(f"   📧 Email: {admin_user.email}")
            print(f"   🔑 Activo: {admin_user.activo} (tipo: {type(admin_user.activo)})")
            print(f"   👤 Rol: {admin_user.rol_nombre}")
            print(f"   🔒 ID: {admin_user.id_usuario}")
            
            # Probar contraseña
            if admin_user.check_password('Admin123!'):
                print("   ✅ Contraseña correcta")
            else:
                print("   ❌ Contraseña incorrecta")
        else:
            print("   ❌ Usuario admin no encontrado")
    except Exception as e:
        print(f"   ❌ Error en login: {e}")
        import traceback
        traceback.print_exc()
    
    # 7. Probar creación de usuario
    print("7. 🧪 Probando creación de usuario:")
    try:
        test_user = Usuario(
            nombre_usuario='test_user',
            email='test@test.com',
            rol_id=4
        )
        test_user.set_password('Test123!')
        print(f"   ✅ Usuario creado: {test_user.nombre_usuario}")
        print(f"   🔑 Password hash: {test_user.password_hash[:50]}...")
        print(f"   👤 Rol ID: {test_user.rol_id}")
        print(f"   ✅ Activo: {test_user.activo}")
    except Exception as e:
        print(f"   ❌ Error creando usuario: {e}")
        import traceback
        traceback.print_exc()
    
    # 8. Verificar variables de entorno
    print("8. 🌍 Variables de entorno:")
    print(f"   - FLASK_ENV: {os.environ.get('FLASK_ENV', 'no definida')}")
    print(f"   - RENDER: {os.environ.get('RENDER', 'no definida')}")
    print(f"   - DATABASE_URL: {'definida' if os.environ.get('DATABASE_URL') else 'no definida'}")
    
    print("\n🏁 FIN DEL DIAGNÓSTICO")
    return True

if __name__ == '__main__':
    debug_system()
