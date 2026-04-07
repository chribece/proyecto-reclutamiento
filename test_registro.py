import os
os.environ['FLASK_ENV'] = 'testing'
os.environ['SECRET_KEY'] = 'test123'

from models import Usuario

# Probar crear un usuario de prueba
try:
    print('🧪 Probando creación de usuario...')
    
    # Crear usuario de prueba
    usuario = Usuario(
        nombre_usuario='testuser123',
        email='testuser123@example.com',
        rol_id=4  # Candidato
    )
    usuario.set_password('testpass123')
    
    # Guardar usuario
    usuario_id = usuario.save()
    print(f'✅ Usuario creado con ID: {usuario_id}')
    
    # Intentar crear el mismo usuario otra vez (debe manejar duplicado)
    try:
        usuario2 = Usuario(
            nombre_usuario='testuser123',
            email='testuser123@example.com',
            rol_id=4
        )
        usuario2.set_password('testpass123')
        usuario_id2 = usuario2.save()
        print(f'⚠️ Usuario duplicado creado con ID: {usuario_id2}')
    except Exception as e:
        print(f'✅ Duplicado manejado correctamente: {str(e)}')
        
except Exception as e:
    print(f'❌ Error al crear usuario: {str(e)}')
    import traceback
    traceback.print_exc()
