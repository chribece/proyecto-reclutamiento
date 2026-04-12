#!/usr/bin/env python3
"""
Diagnóstico específico de autenticación
"""

import os
import sys
from database import db, get_db_type
from models import Usuario

def debug_auth():
    """Diagnóstico completo de autenticación"""
    print("🔍 DIAGNÓSTICO DE AUTENTICACIÓN")
    print("=" * 50)
    
    # 1. Verificar conexión
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
    
    # 2. Verificar tipo de BD
    print(f"2. 🗄️ Tipo de base de datos: {get_db_type()}")
    
    # 3. Verificar tabla usuarios
    print("3. 👥 Estructura de tabla usuarios:")
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
    
    # 4. Verificar usuarios existentes
    print("4. 👤 Usuarios existentes:")
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
                return False
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
        return False
    
    # 5. Probar login admin
    print("5. 🔐 Probando login admin:")
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
                # Verificar hash
                print(f"   🔒 Hash guardado: {admin_user.password_hash[:50]}...")
        else:
            print("   ❌ Usuario admin no encontrado")
    except Exception as e:
        print(f"   ❌ Error en login admin: {e}")
        import traceback
        traceback.print_exc()
    
    # 6. Probar login reclutador
    print("6. 👥 Probando login reclutador:")
    try:
        reclutador_user = Usuario.get_by_email_or_username('reclutador@empresa.com')
        if reclutador_user:
            print(f"   ✅ Usuario encontrado: {reclutador_user.nombre_usuario}")
            print(f"   📧 Email: {reclutador_user.email}")
            print(f"   🔑 Activo: {reclutador_user.activo} (tipo: {type(reclutador_user.activo)})")
            print(f"   👤 Rol: {reclutador_user.rol_nombre}")
            print(f"   🔒 ID: {reclutador_user.id_usuario}")
            
            # Probar contraseña
            if reclutador_user.check_password('Reclutador123!'):
                print("   ✅ Contraseña correcta")
            else:
                print("   ❌ Contraseña incorrecta")
        else:
            print("   ❌ Usuario reclutador no encontrado")
    except Exception as e:
        print(f"   ❌ Error en login reclutador: {e}")
        import traceback
        traceback.print_exc()
    
    # 7. Verificar consulta SQL exacta
    print("7. 🔍 Verificando consulta SQL:")
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Usar valor según tipo de base de datos
            if get_db_type() == 'postgresql':
                active_value = 'TRUE'
            else:
                active_value = '1'
            
            query = f'''
                SELECT u.*, r.nombre as rol_nombre 
                FROM usuarios u
                LEFT JOIN roles r ON u.rol_id = r.id_rol
                WHERE (u.email = %s OR u.nombre_usuario = %s) AND u.activo = {active_value}
                LIMIT 1
            '''
            
            print(f"   📝 Consulta SQL: {query}")
            cursor.execute(query, ('admin@reclutamiento.com', 'admin@reclutamiento.com'))
            result = cursor.fetchone()
            
            if result:
                print(f"   ✅ Resultado encontrado: {result}")
            else:
                print("   ❌ No se encontró resultado")
                
    except Exception as e:
        print(f"   ❌ Error en consulta SQL: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🏁 FIN DEL DIAGNÓSTICO")
    return True

if __name__ == '__main__':
    debug_auth()
