import os
os.environ['FLASK_ENV'] = 'testing'
os.environ['SECRET_KEY'] = 'test123'

print('🔧 Configuración de prueba local...')
print('FLASK_ENV:', os.environ.get('FLASK_ENV'))
print('SECRET_KEY:', os.environ.get('SECRET_KEY'))
print()

from database import db
try:
    print('🔧 Inicializando base de datos SQLite...')
    db.init_database()
    print('✅ Base de datos inicializada correctamente')
    
    # Verificar tablas creadas
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print('📊 Tablas creadas:', [table[0] for table in tables])
        
        # Verificar roles
        cursor.execute('SELECT COUNT(*) as count FROM roles')
        result = cursor.fetchone()
        print('👥 Roles insertados:', result['count'])
        
except Exception as e:
    print('❌ Error en base de datos:', e)
    import traceback
    traceback.print_exc()
