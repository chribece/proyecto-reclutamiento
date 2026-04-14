# 📋 Credenciales de Prueba - Sistema de Reclutamiento

## 🔑 Usuarios del Sistema (Roles Administrativos)

### 👤 Administrador
- **Email**: `admin@reclutamiento.com`
- **Contraseña**: `Admin123!`
- **Rol**: admin
- **Permisos**: Acceso completo a todas las funcionalidades (crear/editar/eliminar vacantes, postulaciones, candidatos, usuarios)

### 👥 Reclutador
- **Email**: `reclutador@empresa.com`
- **Contraseña**: `Reclutador123!`
- **Rol**: reclutador
- **Permisos**: Gestión de cargos (crear/editar), candidatos y postulaciones (crear/editar/activar/desactivar)

### 👔 Gerente
- **Email**: `gerente@empresa.com`
- **Contraseña**: `Gerente123!`
- **Rol**: gerente
- **Permisos**: Gestión de cargos, candidatos y postulaciones + visualización de reportes y estadísticas

## 🎓 Candidatos de Prueba

### Candidato 1
- **Email**: `candidato@ejemplo.com`
- **Contraseña**: `Candidato123!`
- **Rol**: candidato
- **Perfil**: Debe completar perfil antes de ver vacantes o postularse

## 🚀 Cómo Usar

### 1. Para crear los usuarios de prueba:
```bash
python crear_usuarios_prueba.py
```

### 2. Para iniciar sesión:
- Abre la aplicación en tu navegador
- Usa las credenciales según el rol que necesites probar
- Los candidatos también pueden registrarse mediante el formulario público

### 3. Acceso por rol:
- **Administrador**: Puede ver y hacer todo
- **Reclutador**: Puede gestionar cargos y ver candidatos
- **Gerente**: Puede ver reportes y estadísticas
- **Candidato**: Puede ver cargos disponibles y postularse

## 📝 Notas Importantes

- ✅ Todas las contraseñas están hasheadas con PBKDF2-SHA256
- ✅ Los usuarios se crean automáticamente si no existen
- ✅ Los candidatos pueden registrarse libremente por el formulario público
- ✅ El script es compatible con MySQL y SQLite
- ⚠️  **Cambiar las contraseñas en producción antes del despliegue**

## 🔧 Configuración Adicional

### Variables de entorno (opcional):
```bash
# Para especificar la ruta de la base de datos SQLite
SQLITE_DB_PATH=/ruta/personalizada/reclutamiento.db

# Para configurar MySQL (ver config.py)
DATABASE_URL=mysql://usuario:password@host:puerto/database
```

### Para resetear usuarios:
```bash
# Eliminar archivo de base de datos SQLite (si aplica)
rm reclutamiento.db

# Volver a ejecutar el script
python crear_usuarios_prueba.py
```

---
*Generado automáticamente para el Sistema de Reclutamiento*
