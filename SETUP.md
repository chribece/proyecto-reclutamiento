# 🚀 Configuración del Sistema de Reclutamiento

## Requisitos Previos

- MariaDB/MySQL instalado y ejecutándose
- Python 3.8+
- pip (gestor de paquetes de Python)

## Pasos de Instalación

### 1. **Preparar la Base de Datos MariaDB**

```sql
-- Crear la base de datos
CREATE DATABASE reclutamiento CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Crear usuario (opcional si usas root)
CREATE USER 'reclutamiento'@'localhost' IDENTIFIED BY 'tu_contraseña';
GRANT ALL PRIVILEGES ON reclutamiento.* TO 'reclutamiento'@'localhost';
FLUSH PRIVILEGES;
```

### 2. **Instalar Dependencias**

```bash
pip install -r requeriments.txt
```

### 3. **Configurar Variables de Entorno (Opcional)**

Edita `config.py` y ajusta los datos de conexión:

```python
DB_HOST = 'localhost'      # Host de MariaDB
DB_PORT = 3306            # Puerto
DB_USER = 'root'          # Usuario
DB_PASSWORD = ''          # Contraseña
DB_NAME = 'reclutamiento' # Nombre de base de datos
```

**O usa variables de entorno:**

```bash
# En Windows (PowerShell)
$env:DB_HOST = 'localhost'
$env:DB_USER = 'root'
$env:DB_PASSWORD = 'tu_contraseña'
$env:DB_NAME = 'reclutamiento'
```

### 4. **Ejecutar la Aplicación**

```bash
python app.py
```

La aplicación estará disponible en: `http://localhost:5000`

## 🔐 Cambios de Autenticación

### Usuarios y Roles

El sistema ahora tiene **4 roles**:

| Rol | Permisos |
|-----|----------|
| **admin** | Acceso completo a todas las funciones |
| **reclutador** | Gestionar cargos, candidatos y postulaciones |
| **gerente** | Ver reportes y estadísticas de postulaciones |
| **candidato** | Registrarse y ver sus postulaciones |

### Rutas de Autenticación

- **Registro**: `http://localhost:5000/registro`
- **Login**: `http://localhost:5000/login`
- **Logout**: `http://localhost:5000/logout`

### Crear Primer Usuario Administrador

Después de registrarse, abre la BD de MariaDB y ejecuta:

```sql
UPDATE usuarios SET rol_id = 1 WHERE nombre_usuario = 'tu_usuario';
```

O en el registro, selecciona el rol "Administrador".

## 📊 Estructura de Base de Datos

Se han actualizado las siguientes tablas:

### Tabla `usuarios` (Nueva)
```sql
- id_usuario (INT, PK)
- nombre_usuario (VARCHAR 50)
- email (VARCHAR 100)
- password_hash (VARCHAR 255)
- rol_id (INT, FK → roles)
- activo (BOOLEAN)
- created_at (TIMESTAMP)
- ultimo_acceso (TIMESTAMP)
```

### Tabla `roles` (Nueva)
```sql
- id_rol (INT, PK)
- nombre (VARCHAR 50)
- descripcion (TEXT)

Roles predefinidos:
1. admin
2. reclutador
3. gerente
4. candidato
```

### Tabla `cargos` (Actualizada)
```sql
- id_cargo (INT, PK) ← antiguamente: id
- nombre (VARCHAR) ← antiguamente: titulo
- descripcion (TEXT)
- departamento (VARCHAR)
- salario_minimo (DECIMAL)
- salario_maximo (DECIMAL)
- tipo_contrato (VARCHAR)
- ubicacion (VARCHAR)
- estado (VARCHAR)
- fecha_creacion (TIMESTAMP)
- fecha_cierre (DATE)
```

### Tabla `postulaciones` (Actualizada)
```sql
- id_postulacion (INT, PK) ← antiguamente: id
- cedula (VARCHAR 10, FK → candidatos)
- id_cargo (INT, FK → cargos) ← antiguamente: cargo_id
- fecha_postulacion (TIMESTAMP)
- estado (VARCHAR)
- fuente_reclutamiento (VARCHAR)
- notas (TEXT)
- puntaje_evaluacion (INT)
- fecha_actualizacion (TIMESTAMP)
```

## 🔧 Migrarmación desde SQLite (Si tenías datos antiguos)

Si tenías datos en SQLite y quieres migrar:

1. **Exportar datos de SQLite**
2. **Importar a MariaDB** usando herramientas como HeidiSQL o MySQL Workbench

## ⚠️ Errores Comunes

### Error: "Access denied for user 'root'@'localhost'"
- Verifica que MariaDB está ejecutándose
- Comprueba el usuario y contraseña en `config.py`

### Error: "No module named 'pymysql'"
```bash
pip install PyMySQL
```

### Error: "Base de datos no encontrada"
```sql
CREATE DATABASE reclutamiento CHARACTER SET utf8mb4;
```

## 📝 Notas Importantes

1. **Seguridad**: Las contraseñas se hashean con PBKDF2
2. **Base de Datos**: Se usa INNODB con soporte para caracteres UTF-8
3. **Validación**: Se validan roles en cada ruta protegida
4. **Sesiones**: Se mantienen durante 1 hora (configurable en `config.py`)

## 🆘 Soporte

Si encuentras problemas:
1. Verifica que MariaDB está corriendo
2. Revisa los logs de Flask
3. Comprueba que todas las dependencias están instaladas

¡Éxito con tu sistema de reclutamiento! 🎉
