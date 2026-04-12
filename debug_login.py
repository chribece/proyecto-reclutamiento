#!/usr/bin/env python3
"""
Script para debuggear el problema de login en producción
"""

import os
from database import db, get_db_type
from models import Usuario

def debug_database():
    """Verifica el estado de la base de datos"""
    print(f"🔍 Debug de Base de Datos")
    print(f"Tipo de BD: {get_db_type()}")
    print(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
    print()
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Verificar tablas
            print("📋 Tablas en la base de datos:")
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            tablas = cursor.fetchall()
            for tabla in tablas:
                nombre = tabla[0] if isinstance(tabla, (tuple, list)) else tabla.get('table_name')
                print(f"  - {nombre}")
            print()
            
            # 2. Verificar usuarios
            print("👥 Usuarios en la base de datos:")
            cursor.execute("""
                SELECT u.id_usuario, u.nombre_usuario, u.email, u.activo, u.rol_id, r.nombre as rol_nombre
                FROM usuarios u
                LEFT JOIN roles r ON u.rol_id = r.id_rol
                ORDER BY u.id_usuario
            """)
            usuarios = cursor.fetchall()
            
            if not usuarios:
                print("  ❌ No hay usuarios en la base de datos")
                print("  🔄 Ejecutando inicialización...")
                from init_produccion import inicializar_produccion
                inicializar_produccion()
                return
            
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
                
                print(f"  ID: {id_u}")
                print(f"  Nombre: {nombre}")
                print(f"  Email: {email}")
                print(f"  Activo: {activo} (tipo: {type(activo)})")
                print(f"  Rol ID: {rol_id}")
                print(f"  Rol Nombre: {rol_nombre}")
                print("  ---")
            print()
            
            # 3. Probar login específico
            print("🔐 Probando login con admin@reclutamiento.com:")
            try:
                admin_user = Usuario.get_by_email_or_username('admin@reclutamiento.com')
                if admin_user:
                    print(f"  ✅ Usuario encontrado: {admin_user.nombre_usuario}")
                    print(f"  📧 Email: {admin_user.email}")
                    print(f"  🔑 Activo: {admin_user.activo} (tipo: {type(admin_user.activo)})")
                    print(f"  👤 Rol: {admin_user.rol_nombre}")
                    
                    # Probar contraseña
                    if admin_user.check_password('Admin123!'):
                        print("  ✅ Contraseña correcta")
                    else:
                        print("  ❌ Contraseña incorrecta")
                else:
                    print("  ❌ Usuario no encontrado")
            except Exception as e:
                print(f"  ❌ Error en login: {e}")
                import traceback
                traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()

def test_connection():
    """Prueba la conexión a la base de datos"""
    print("🔌 Probando conexión a la base de datos...")
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            print(f"✅ Conexión exitosa: {result}")
            return True
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

if __name__ == '__main__':
    print("🐛 Debug Login - Sistema de Reclutamiento")
    print("=" * 50)
    
    if test_connection():
        debug_database()
    
    print("\n🏁 Fin del debug")
