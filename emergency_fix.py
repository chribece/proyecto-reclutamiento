#!/usr/bin/env python3
"""
Fix de emergencia para errores de login en producción
"""

import os
from database import db

def emergency_fix():
    """Fix de emergencia para problemas críticos"""
    print("🚨 EMERGENCY FIX - Sistema de Reclutamiento")
    print("=" * 60)
    
    try:
        # 1. Verificar conexión básica
        print("1. Verificando conexión a la base de datos...")
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            print(f"   ✅ Conexión OK: {result}")
        
        # 2. Verificar tablas críticas
        print("\n2. Verificando tablas críticas...")
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar tabla usuarios
            try:
                cursor.execute("SELECT COUNT(*) as count FROM usuarios")
                count = cursor.fetchone()
                if isinstance(count, dict):
                    user_count = count.get('count', 0)
                else:
                    user_count = count[0] if count else 0
                print(f"   👥 Tabla usuarios: {user_count} registros")
            except Exception as e:
                print(f"   ❌ Error tabla usuarios: {e}")
            
            # Verificar tabla roles
            try:
                cursor.execute("SELECT COUNT(*) as count FROM roles")
                count = cursor.fetchone()
                if isinstance(count, dict):
                    role_count = count.get('count', 0)
                else:
                    role_count = count[0] if count else 0
                print(f"   🎭 Tabla roles: {role_count} registros")
            except Exception as e:
                print(f"   ❌ Error tabla roles: {e}")
        
        # 3. Crear usuario admin si no existe
        print("\n3. Verificando usuario administrador...")
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Buscar admin por email
            try:
                cursor.execute("SELECT * FROM usuarios WHERE email = %s LIMIT 1", ('admin@reclutamiento.com',))
                admin = cursor.fetchone()
                
                if not admin:
                    print("   🔄 Creando usuario administrador...")
                    
                    # Insertar admin manualmente
                    cursor.execute("""
                        INSERT INTO usuarios (nombre_usuario, email, password_hash, rol_id, activo, created_at)
                        VALUES (%s, %s, %s, %s, %s, NOW())
                    """, (
                        'admin',
                        'admin@reclutamiento.com',
                        'pbkdf2:sha256:260000$...',  # Placeholder - se actualizará después
                        1,  # rol_id = 1 (admin)
                        True  # activo
                    ))
                    conn.commit()
                    print("   ✅ Usuario admin creado")
                    
                    # Actualizar contraseña correctamente
                    from werkzeug.security import generate_password_hash
                    password_hash = generate_password_hash('Admin123!', method='pbkdf2:sha256')
                    cursor.execute("""
                        UPDATE usuarios SET password_hash = %s WHERE email = %s
                    """, (password_hash, 'admin@reclutamiento.com'))
                    conn.commit()
                    print("   ✅ Contraseña admin actualizada")
                    
                else:
                    print("   ✅ Usuario admin ya existe")
                    
                    # Verificar contraseña
                    if isinstance(admin, dict):
                        password_hash = admin.get('password_hash', '')
                    else:
                        password_hash = admin[4] if len(admin) > 4 else ''
                    
                    if not password_hash or '...' in password_hash:
                        print("   🔄 Actualizando contraseña admin...")
                        from werkzeug.security import generate_password_hash
                        password_hash = generate_password_hash('Admin123!', method='pbkdf2:sha256')
                        cursor.execute("""
                            UPDATE usuarios SET password_hash = %s WHERE email = %s
                        """, (password_hash, 'admin@reclutamiento.com'))
                        conn.commit()
                        print("   ✅ Contraseña admin actualizada")
                        
            except Exception as e:
                print(f"   ❌ Error creando admin: {e}")
        
        print("\n✅ Emergency fix completado")
        print("🔑 Credenciales:")
        print("   Email: admin@reclutamiento.com")
        print("   Contraseña: Admin123!")
        print("   Rol: Administrador")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error en emergency fix: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    emergency_fix()
