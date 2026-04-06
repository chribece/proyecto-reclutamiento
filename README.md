# 🏢 Sistema de Reclutamiento GF

Un sistema web completo para la gestión de procesos de reclutamiento y selección de personal, desarrollado con Flask y MySQL.

## 🚀 Características Principales

### 👥 Gestión de Candidatos
- Registro y perfil completo de candidatos
- Subida de documentos (CVs)
- Seguimiento de disponibilidad
- Búsqueda avanzada por habilidades y filtros

### 💼 Gestión de Cargos
- Creación y edición de posiciones
- Definición de requerimientos por cargo
- Clasificación por tipo de contrato

### 📋 Gestión de Postulaciones
- Seguimiento completo del pipeline
- Estados personalizables (Recibido, En revisión, Entrevista, etc.)
- Sistema de evaluación con puntaje
- Notas y comentarios por postulación
- Activación/Desactivación de postulaciones

### 👤 Gestión de Usuarios
- Roles basados en permisos (Admin, Reclutador, Gerente, Candidato)
- Sistema de autenticación seguro
- Control de acceso granular

### 📊 Reportes y Estadísticas
- Reportes PDF de candidatos y postulaciones
- Estadísticas del pipeline de reclutamiento
- Métricas de tiempo de contratación

## 🛠️ Stack Tecnológico

- **Backend**: Flask 3.1.3
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap
- **Base de Datos**: MySQL/MariaDB
- **Autenticación**: Flask-Login
- **Formularios**: Flask-WTF
- **PDF Generation**: ReportLab
- **Servidor de Producción**: Gunicorn

## 📁 Estructura del Proyecto

```
proyecto-reclutamiento/
├── app.py                 # Aplicación principal Flask
├── config.py             # Configuración de la aplicación
├── database.py           # Conexión a base de datos
├── models.py             # Modelos de datos
├── forms.py              # Formularios WTForms
├── utils.py              # Utilidades y funciones helper
├── requirements.txt      # Dependencias Python
├── Procfile             # Configuración de deploy
├── runtime.txt          # Versión de Python
├── static/              # Archivos estáticos
│   ├── css/            # Hojas de estilo
│   ├── js/             # Scripts JavaScript
│   └── Img/            # Imágenes y logos
└── templates/          # Plantillas Jinja2
    ├── base.html       # Plantilla base
    ├── admin/          # Templates de administración
    ├── candidatos/     # Templates de candidatos
    ├── postulaciones/  # Templates de postulaciones
    └── cargos/         # Templates de cargos
```

## 🚀 Instalación y Configuración

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/proyecto-reclutamiento.git
cd proyecto-reclutamiento
```

### 2. Crear entorno virtual
```bash
python -m venv venv
# En Windows
venv\Scripts\activate
# En macOS/Linux
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar base de datos
- Crear base de datos MySQL llamada `reclutamiento`
- Configurar variables de entorno o modificar `config.py`

### 5. Ejecutar la aplicación
```bash
python app.py
```

## 🔧 Variables de Entorno

```bash
# Base de Datos
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=tu_contraseña
DB_NAME=reclutamiento

# Aplicación
SECRET_KEY=tu_clave_secreta
FLASK_DEBUG=False
SESSION_COOKIE_SECURE=True
```

## 🌐 Deploy en Render.com

El proyecto está configurado para deploy automático en Render.com:

1. **Conectar repositorio** a Render.com
2. **Configurar variables de entorno** en el dashboard
3. **Deploy automático** con los archivos:
   - `requirements.txt` - Dependencias
   - `Procfile` - Configuración Gunicorn
   - `runtime.txt` - Python 3.11.0

## 📱 Funcionalidades Detalladas

### Gestión de Candidatos
- ✅ Registro completo con información personal
- ✅ Subida de documentos (CVs, certificados)
- ✅ Historial educativo y laboral
- ✅ Referencias personales
- ✅ Búsqueda por nombre, email, habilidades
- ✅ Filtros por disponibilidad y estado

### Pipeline de Postulaciones
- ✅ Estados personalizables
- ✅ Sistema de evaluación (1-10 puntos)
- ✅ Notas y seguimiento
- ✅ Activación/Desactivación
- ✅ Paginación avanzada
- ✅ Filtros por estado y activación

### Sistema de Roles
- **Admin**: Acceso completo a todas las funciones
- **Reclutador**: Gestión de candidatos y postulaciones
- **Gerente**: Reportes y estadísticas
- **Candidato**: Perfil limitado y aplicaciones

## 🎨 Interfaz de Usuario

- ✅ Diseño responsive y moderno
- ✅ Sistema de colores corporativos GF
- ✅ Navegación intuitiva
- ✅ Formularios validados
- ✅ Notificaciones y mensajes flash
- ✅ Paginación avanzada con puntos suspensivos

## 📊 Reportes

- ✅ Reporte PDF de candidatos
- ✅ Reporte PDF de postulaciones
- ✅ Estadísticas del pipeline
- ✅ Métricas de tiempo de contratación

## 🔒 Seguridad

- ✅ Autenticación con Flask-Login
- ✅ Hashing de contraseñas
- ✅ Protección CSRF
- ✅ Validación de entrada
- ✅ Sesiones seguras
- ✅ Control de acceso por roles

## 🤝 Contribución

1. Fork del proyecto
2. Crear feature branch (`git checkout -b feature/NuevaFuncionalidad`)
3. Commit de cambios (`git commit -m 'Agrega nueva funcionalidad'`)
4. Push al branch (`git push origin feature/NuevaFuncionalidad`)
5. Pull Request

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT.

## 👥 Autores

- **[Tu Nombre]** - *Desarrollo inicial* - [TuGitHub]

---

🏢 **GF Reclutamiento** - Transformando la gestión de talento humano
