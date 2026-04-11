# 🔧 Guía de Solución de Problemas - Login

## ❌ Problema: "No puedo acceder con las credenciales"

### ✅ Verificación Rápida

1. **Ejecuta el script de prueba:**
```bash
python test_login.py
```
Si todos los usuarios muestran "✅ Login exitoso", las credenciales son correctas.

2. **Inicia la aplicación:**
```bash
python app.py
```
Deberías ver algo como:
```
* Running on http://127.0.0.1:5000
* Debug mode: on
```

### 🔍 Problemas Comunes y Soluciones

#### 1. **Aplicación no está corriendo**
- **Síntoma**: "No se puede acceder a la página"
- **Solución**: Asegúrate de ejecutar `python app.py` y esperar el mensaje "Running on..."

#### 2. **Base de datos incorrecta**
- **Síntoma**: Login falla pero `test_login.py` funciona
- **Solución**: 
```bash
python crear_usuarios_prueba.py
python actualizar_bd.py
```

#### 3. **Contraseña incorrecta**
- **Síntoma**: Mensaje de "Contraseña incorrecta"
- **Solución**: Copia y pega las contraseñas exactas:
  - Admin: `Admin123!`
  - Reclutador: `Reclu123!`
  - Gerente: `Gerente123!`
  - Candidato1: `Candidato1!`
  - Candidato2: `Candidato2!`

#### 4. **Email incorrecto**
- **Síntoma**: Mensaje de "Usuario no encontrado"
- **Solución**: Usa los emails exactos:
  - `admin@reclutamiento.com`
  - `reclutador@reclutamiento.com`
  - `gerente@reclutamiento.com`
  - `juan.perez@email.com`
  - `maria.garcia@email.com`

### 🚀 Pasos para Iniciar Sesión

1. **Inicia la aplicación:**
```bash
cd "c:\Users\Paola\Documents\UEA_4\Desarrollo de aplicaciones web\2526-DESARROLLO-DE-APLICACIONES-WEB\proyecto-reclutamiento"
python app.py
```

2. **Abre el navegador:**
   - Ve a `http://127.0.0.1:5000`

3. **Usa las credenciales:**
   - Email: `admin@reclutamiento.com`
   - Contraseña: `Admin123!`

### 🧪 Si todo falla, prueba con:

```python
from models import Usuario
from werkzeug.security import check_password_hash

# Prueba directa
user = Usuario.get_by_email_or_username('admin@reclutamiento.com')
if user and user.check_password('Admin123!'):
    print("✅ Credenciales correctas")
else:
    print("❌ Credenciales incorrectas")
```

### 📞 Si el problema persiste:

1. Verifica que no haya errores en la consola al ejecutar `app.py`
2. Limpia el caché del navegador
3. Intenta en modo incógnito
4. Reinicia la aplicación completamente

---
*Si sigues con problemas, ejecuta `test_login.py` y muestra el resultado*
