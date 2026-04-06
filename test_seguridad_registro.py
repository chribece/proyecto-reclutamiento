#!/usr/bin/env python3
"""
TEST DE SEGURIDAD - Registro de Usuarios
========================================
Verifica que no sea posible registrar usuarios con roles privilegiados
desde el formulario público de registro.
"""

import requests
import json
import sys

BASE_URL = "http://127.0.0.1:5000"

def test_registro_publico_seguridad():
    """Test de seguridad para registro público"""
    print("🔒 TEST DE SEGURIDAD - Registro Público")
    print("=" * 50)
    
    # Test cases con diferentes intentos de manipulación
    test_cases = [
        {
            "name": "Intento de registro como Administrador",
            "email": "test_admin@malicioso.com",
            "password": "test123",
            "password_confirm": "test123",
            "rol": "1"  # Administrador
        },
        {
            "name": "Intento de registro como Reclutador", 
            "email": "test_reclutador@malicioso.com",
            "password": "test123",
            "password_confirm": "test123",
            "rol": "2"  # Reclutador
        },
        {
            "name": "Intento de registro como Gerente RRHH",
            "email": "test_gerente@malicioso.com", 
            "password": "test123",
            "password_confirm": "test123",
            "rol": "3"  # Gerente RRHH
        },
        {
            "name": "Registro normal como Candidato (debe funcionar)",
            "email": "test_candidato@normal.com",
            "password": "test123", 
            "password_confirm": "test123",
            "rol": "4"  # Candidato
        }
    ]
    
    resultados = []
    
    for test_case in test_cases:
        print(f"\n🧪 {test_case['name']}")
        print(f"   Email: {test_case['email']}")
        print(f"   Rol: {test_case['rol']}")
        
        try:
            # Obtener CSRF token
            session = requests.Session()
            response = session.get(f"{BASE_URL}/registro")
            
            if response.status_code != 200:
                print(f"   ❌ Error obteniendo página de registro: {response.status_code}")
                continue
            
            # Extraer CSRF token (simplificado)
            csrf_token = "test_token"  # En producción, extraer del HTML
            
            # Intentar registro
            data = {
                "email": test_case["email"],
                "password": test_case["password"], 
                "password_confirm": test_case["password_confirm"],
                "rol": test_case["rol"],
                "csrf_token": csrf_token
            }
            
            response = session.post(f"{BASE_URL}/registro", data=data)
            
            # Verificar resultado
            if test_case["rol"] == "4":  # Candidato - debería funcionar
                if response.status_code == 200:
                    print("   ✅ Registro como Candidato permitido (correcto)")
                    resultados.append(True)
                else:
                    print(f"   ❌ Registro como Candidato bloqueado (incorrecto): {response.status_code}")
                    resultados.append(False)
            else:  # Roles privilegiados - deberían ser bloqueados
                if response.status_code == 200 and "error" in response.text.lower():
                    print("   ✅ Intento de rol privilegiado bloqueado (correcto)")
                    resultados.append(True)
                else:
                    print(f"   ❌ Intento de rol privilegiado permitido (INCORRECTO): {response.status_code}")
                    resultados.append(False)
                    
        except Exception as e:
            print(f"   ❌ Error en la prueba: {e}")
            resultados.append(False)
    
    # Resumen
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE RESULTADOS")
    print("=" * 50)
    
    exitosos = sum(resultados)
    total = len(resultados)
    
    print(f"Tests exitosos: {exitosos}/{total}")
    
    if exitosos == total:
        print("✅ Todos los tests de seguridad pasaron")
        print("🛡️ El sistema es seguro contra manipulación de roles")
        return True
    else:
        print("❌ Hay vulnerabilidades de seguridad")
        print("⚠️ Se requiere revisión inmediata")
        return False

def test_base_datos_seguridad():
    """Verificar que la base de datos no tenga usuarios con roles incorrectos"""
    print("\n🗄️ TEST DE BASE DE DATOS")
    print("=" * 30)
    
    try:
        from database import db
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar que no haya usuarios creados con roles privilegiados desde registro público
            cursor.execute('''
                SELECT email, rol_id, created_at 
                FROM usuarios 
                WHERE rol_id IN (1, 2, 3) 
                AND created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
                ORDER BY created_at DESC
            ''')
            
            usuarios_privilegiados_recientes = cursor.fetchall()
            
            if usuarios_privilegiados_recientes:
                print("❌ Usuarios con roles privilegiados creados recientemente:")
                for usuario in usuarios_privilegiados_recientes:
                    print(f"   - {usuario['email']} (Rol: {usuario['rol_id']}, Creado: {usuario['created_at']})")
                return False
            else:
                print("✅ No hay usuarios privilegiados creados recientemente")
                return True
                
    except Exception as e:
        print(f"❌ Error verificando base de datos: {e}")
        return False

if __name__ == "__main__":
    print("🔍 INICIANDO TESTS DE SEGURIDAD")
    print("=" * 50)
    
    # Ejecutar tests
    test1_resultado = test_registro_publico_seguridad()
    test2_resultado = test_base_datos_seguridad()
    
    # Resultado final
    print("\n" + "=" * 50)
    print("🏁 RESULTADO FINAL")
    print("=" * 50)
    
    if test1_resultado and test2_resultado:
        print("✅ Todos los tests de seguridad pasaron")
        print("🛡️ El sistema está seguro")
        sys.exit(0)
    else:
        print("❌ Se detectaron vulnerabilidades de seguridad")
        print("⚠️ Requerida acción inmediata")
        sys.exit(1)
