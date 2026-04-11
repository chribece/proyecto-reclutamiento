#!/usr/bin/env python3
"""
Script para probar el login de usuarios
"""

from models import Usuario
from werkzeug.security import check_password_hash

def probar_login():
    """Prueba el login con las credenciales del archivo CREDENCIALES_PRUEBA.md"""
    
    print("🔐 Probando login con credenciales de prueba\n")
    
    usuarios_prueba = [
        ('admin@reclutamiento.com', 'Admin123!', 'Administrador'),
        ('reclutador@reclutamiento.com', 'Reclu123!', 'Reclutador'),
        ('gerente@reclutamiento.com', 'Gerente123!', 'Gerente'),
        ('juan.perez@email.com', 'Candidato1!', 'Candidato'),
        ('maria.garcia@email.com', 'Candidato2!', 'Candidato')
    ]
    
    for email, password, rol in usuarios_prueba:
        print(f"👤 Probando {rol}: {email}")
        
        # Buscar usuario
        usuario = Usuario.get_by_email_or_username(email)
        
        if not usuario:
            print(f"   ❌ Usuario no encontrado")
            continue
        
        # Verificar contraseña
        if usuario.check_password(password):
            print(f"   ✅ Login exitoso")
            print(f"   📋 Nombre: {usuario.nombre_usuario}")
            print(f"   🏷️  Rol: {usuario.rol_nombre}")
            print(f"   📧 Email: {usuario.email}")
        else:
            print(f"   ❌ Contraseña incorrecta")
        
        print()

if __name__ == "__main__":
    probar_login()
