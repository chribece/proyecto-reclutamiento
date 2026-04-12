#!/usr/bin/env python3
"""
Diagnóstico específico para producción
"""

import os
import sys

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_production():
    """Diagnóstico completo para producción"""
    print("PRODUCTION DEBUG - DIAGNÓSTICO COMPLETO")
    print("=" * 60)
    
    try:
        # 1. Importaciones básicas
        print("1. Importando módulos...")
        from database import db, get_db_type
        print("   - database.py: OK")
        
        from models import Usuario
        print("   - models.py: OK")
        
        from werkzeug.security import generate_password_hash, check_password_hash
        print("   - werkzeug.security: OK")
        
        # 2. Conexión a BD
        print("2. Probando conexión a BD...")
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 as test, NOW() as tiempo")
                result = cursor.fetchone()
                print(f"   - Conexión OK: {result}")
        except Exception as e:
            print(f"   - ERROR conexión: {e}")
            return False
        
        # 3. Tipo de BD
        print(f"3. Tipo de BD: {get_db_type()}")
        
        # 4. Verificar tabla usuarios
        print("4. Verificando tabla usuarios...")
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
                print(f"   - Columnas encontradas: {len(columnas)}")
                for col in columnas:
                    if isinstance(col, (tuple, list)):
                        print(f"     * {col[0]}: {col[1]} (default: {col[2]}, nullable: {col[3]})")
                    else:
                        print(f"     * {col.get('column_name')}: {col.get('data_type')}")
        except Exception as e:
            print(f"   - ERROR verificando tabla: {e}")
            return False
        
        # 5. Verificar tabla roles
        print("5. Verificando tabla roles...")
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM roles")
                result = cursor.fetchone()
                count = result['count'] if isinstance(result, dict) else result[0]
                print(f"   - Roles existentes: {count}")
                
                if count > 0:
                    cursor.execute("SELECT id_rol, nombre FROM roles ORDER BY id_rol")
                    roles = cursor.fetchall()
                    for rol in roles:
                        if isinstance(rol, (tuple, list)):
                            print(f"     * ID: {rol[0]}, Nombre: {rol[1]}")
                        else:
                            print(f"     * ID: {rol.get('id_rol')}, Nombre: {rol.get('nombre')}")
        except Exception as e:
            print(f"   - ERROR verificando roles: {e}")
        
        # 6. Verificar usuarios existentes
        print("6. Verificando usuarios existentes...")
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
                
                print(f"   - Usuarios encontrados: {len(usuarios)}")
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
                    
                    print(f"     * ID: {id_u}, Nombre: {nombre}, Email: {email}, Activo: {activo} ({type(activo)}), Rol: {rol_nombre}")
        except Exception as e:
            print(f"   - ERROR verificando usuarios: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # 7. Probar Usuario.get_by_email_or_username
        print("7. Probando Usuario.get_by_email_or_username...")
        try:
            admin_user = Usuario.get_by_email_or_username('admin@reclutamiento.com')
            if admin_user:
                print(f"   - Usuario encontrado: {admin_user.nombre_usuario}")
                print(f"     Email: {admin_user.email}")
                print(f"     Activo: {admin_user.activo} (tipo: {type(admin_user.activo)})")
                print(f"     Rol: {admin_user.rol_nombre}")
                print(f"     ID: {admin_user.id_usuario}")
                print(f"     Password hash: {admin_user.password_hash[:50]}...")
                
                # Probar contraseña
                if admin_user.check_password('Admin123!'):
                    print("   - Contraseña correcta")
                else:
                    print("   - Contraseña incorrecta")
                    # Probar hash manualmente
                    test_hash = generate_password_hash('Admin123!', method='pbkdf2:sha256')
                    print(f"   - Hash de prueba: {test_hash[:50]}...")
            else:
                print("   - Usuario admin NO encontrado")
        except Exception as e:
            print(f"   - ERROR en get_by_email_or_username: {e}")
            import traceback
            traceback.print_exc()
        
        # 8. Probar consulta SQL manual
        print("8. Probando consulta SQL manual...")
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
                
                print(f"   - Consulta: {query}")
                cursor.execute(query, ('admin@reclutamiento.com', 'admin@reclutamiento.com'))
                result = cursor.fetchone()
                
                if result:
                    print(f"   - Resultado encontrado: {result}")
                else:
                    print("   - NO se encontró resultado")
                    
        except Exception as e:
            print(f"   - ERROR en consulta manual: {e}")
            import traceback
            traceback.print_exc()
        
        # 9. Verificar variables de entorno
        print("9. Variables de entorno:")
        print(f"   - FLASK_ENV: {os.environ.get('FLASK_ENV', 'no definida')}")
        print(f"   - RENDER: {os.environ.get('RENDER', 'no definida')}")
        print(f"   - DATABASE_URL: {'definida' if os.environ.get('DATABASE_URL') else 'no definida'}")
        
        print("\nDIAGNÓSTICO COMPLETADO")
        return True
        
    except Exception as e:
        print(f"ERROR GENERAL: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    debug_production()
