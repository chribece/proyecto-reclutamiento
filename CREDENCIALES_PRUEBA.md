# 📋 Credenciales de Prueba - Sistema de Reclutamiento

## 🔑 Usuarios del Sistema (Roles Administrativos)

### 👤 Administrador
- **Email**: `  `
- **Contraseña**: `Admin123!`
- **Rol**: Administrador del sistema
- **Permisos**: Acceso completo a todas las funcionalidades

### 👥 Reclutador
- **Email**: `reclutador@reclutamiento.com`
- **Contraseña**: `Reclu123!`
- **Rol**: Reclutador
- **Permisos**: Gestión de cargos, candidatos y postulaciones

### 👔 Gerente de RRHH
- **Email**: `gerente@reclutamiento.com`
- **Contraseña**: ` `
- **Rol**: Gerente
- **Permisos**: Visualización de reportes y estadísticas

## 🎓 Candidatos de Prueba

### Candidato 1 - Desarrollador
- **Email**: `juan.perez@email.com`
- **Contraseña**: `Candidato1!`
- **Cédula**: `1234567890`
- **Perfil**: Desarrollador Python con 5 años de experiencia

### Candidato 2 - Diseñadora
- **Email**: `maria.garcia@email.com`
- **Contraseña**: `Candidato2!`
- **Cédula**: `0987654321`
- **Perfil**: Diseñadora UX/UI con 3 años de experiencia

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
