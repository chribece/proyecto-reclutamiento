from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from config import Config
from database import db
from report_generator import report_generator, create_pdf_response
from models import Cargo, Candidato, Postulacion, EstadisticasRRHH, Usuario, Referencia, Experiencia
from forms import CargoForm, CandidatoForm, CandidatoRegistroForm, PostulacionForm, BusquedaCandidatoForm, LoginForm, RegisterForm, ReferenciaForm, ExperienciaForm
from utils import formatear_fecha, calcular_match, EstadoPipeline
from datetime import datetime
import os
from functools import wraps

# Fix de emergencia para autenticación
try:
    from emergency_auth_fix import emergency_auth_fix
    print(" Ejecutando fix de emergencia para autenticación...")
    emergency_auth_fix()
    print(" Fix de autenticación completado")
except Exception as e:
    print(f" Error en fix de autenticación: {e}")

app = Flask(__name__)
app.config.from_object(Config)

# Inicialización automática para producción (Render)
# Simplificado para evitar errores en health check
if os.environ.get('FLASK_ENV') == 'production' and os.environ.get('RENDER'):
    try:
        import threading
        def init_thread():
            try:
                from init_produccion import inicializar_produccion
                inicializar_produccion()
                print("✅ Producción inicializada")
            except Exception as e:
                print(f"⚠️ Error en inicialización: {e}")
        
        # Inicializar en thread separado para no bloquear el inicio
        threading.Thread(target=init_thread, daemon=True).start()
    except Exception as e:
        print(f"⚠️ Error configurando inicialización: {e}")

# Migración automática: agregar fecha_actualizacion a postulaciones si no existe
def migrar_fecha_actualizacion():
    """Migración automática para agregar columna fecha_actualizacion"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            db_type = db.db_type
            
            if db_type == 'postgresql':
                # Verificar si columna existe en PostgreSQL
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='postulaciones' AND column_name='fecha_actualizacion'
                """)
                if not cursor.fetchone():
                    print("🔄 Migrando: Agregando columna fecha_actualizacion a postulaciones...")
                    cursor.execute("ALTER TABLE postulaciones ADD COLUMN fecha_actualizacion TIMESTAMP")
                    conn.commit()
                    print("✅ Migración completada: fecha_actualizacion agregada")
                else:
                    print("✓ Columna fecha_actualizacion ya existe")
            elif db_type == 'sqlite':
                # SQLite: verificar con PRAGMA
                cursor.execute("PRAGMA table_info(postulaciones)")
                columns = [row['name'] for row in cursor.fetchall()]
                if 'fecha_actualizacion' not in columns:
                    print("🔄 Migrando: Agregando columna fecha_actualizacion a postulaciones...")
                    cursor.execute("ALTER TABLE postulaciones ADD COLUMN fecha_actualizacion TIMESTAMP")
                    conn.commit()
                    print("✅ Migración completada: fecha_actualizacion agregada")
                else:
                    print("✓ Columna fecha_actualizacion ya existe")
            else:
                # MySQL y otros
                try:
                    cursor.execute("ALTER TABLE postulaciones ADD COLUMN fecha_actualizacion TIMESTAMP")
                    conn.commit()
                    print("✅ Migración completada: fecha_actualizacion agregada")
                except Exception as e:
                    if 'Duplicate' in str(e) or 'exists' in str(e).lower():
                        print("✓ Columna fecha_actualizacion ya existe")
                    else:
                        raise
    except Exception as e:
        print(f"⚠️ Error en migración fecha_actualizacion: {e}")

# Migración automática: agregar activo a postulaciones si no existe
def migrar_activo_postulaciones():
    """Migración automática para agregar columna activo"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            db_type = db.db_type
            
            if db_type == 'postgresql':
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='postulaciones' AND column_name='activo'
                """)
                if not cursor.fetchone():
                    print("🔄 Migrando: Agregando columna activo a postulaciones...")
                    cursor.execute("ALTER TABLE postulaciones ADD COLUMN activo BOOLEAN DEFAULT TRUE")
                    conn.commit()
                    print("✅ Migración completada: activo agregado")
                else:
                    print("✓ Columna activo ya existe")
            elif db_type == 'sqlite':
                cursor.execute("PRAGMA table_info(postulaciones)")
                columns = [row['name'] for row in cursor.fetchall()]
                if 'activo' not in columns:
                    print("🔄 Migrando: Agregando columna activo a postulaciones...")
                    cursor.execute("ALTER TABLE postulaciones ADD COLUMN activo BOOLEAN DEFAULT 1")
                    conn.commit()
                    print("✅ Migración completada: activo agregado")
                else:
                    print("✓ Columna activo ya existe")
            else:
                try:
                    cursor.execute("ALTER TABLE postulaciones ADD COLUMN activo BOOLEAN DEFAULT TRUE")
                    conn.commit()
                    print("✅ Migración completada: activo agregado")
                except Exception as e:
                    if 'Duplicate' in str(e) or 'exists' in str(e).lower():
                        print("✓ Columna activo ya existe")
                    else:
                        raise
    except Exception as e:
        print(f"⚠️ Error en migración activo: {e}")

# Ejecutar migraciones al inicio
try:
    migrar_fecha_actualizacion()
    migrar_activo_postulaciones()
except Exception as e:
    print(f"⚠️ Error ejecutando migración: {e}")

# Configurar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor inicia sesión para acceder a esta página'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return Usuario.get_by_id(int(user_id))

@app.before_request
def init_db():
    if not hasattr(app, 'db_initialized'):
        db.init_database()
        app.db_initialized = True

@app.context_processor
def inject_globals():
    from datetime import date
    return {
        'colors': Config.COLORS,
        'formatear_fecha': formatear_fecha,
        'hoy': date.today()
    }

# ============ DECORADORES DE ROLES ============
def require_role(roles):
    """Decorador para verificar roles"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Por favor inicia sesión', 'warning')
                return redirect(url_for('login'))
            print(f"DEBUG ROLE: Usuario={current_user.nombre_usuario}, rol_nombre='{current_user.rol_nombre}', Requerido={roles}")
            if current_user.rol_nombre not in roles:
                flash(f'No tienes permiso para acceder a esta página (rol: {current_user.rol_nombre})', 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ============ RUTAS DE AUTENTICACIÓN ============
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        print("LOGIN DEBUG: Usuario ya autenticado, redirigiendo a index")
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        try:
            print(f"LOGIN DEBUG: Intentando login con email: {form.email.data}")
            
            # Buscar por email O nombre_usuario
            usuario = Usuario.get_by_email_or_username(form.email.data)
            print(f"LOGIN DEBUG: Usuario encontrado: {usuario is not None}")
            
            if usuario:
                print(f"LOGIN DEBUG: Usuario datos - ID: {usuario.id_usuario}, Nombre: {usuario.nombre_usuario}, Activo: {usuario.activo}, Rol: {usuario.rol_nombre}")
                
                # Probar contraseña
                password_check = usuario.check_password(form.password.data)
                print(f"LOGIN DEBUG: Contraseña correcta: {password_check}")
                
                if password_check:
                    print("LOGIN DEBUG: Login exitoso, iniciando sesión...")
                    login_user(usuario, remember=True)
                    print("LOGIN DEBUG: Sesión iniciada correctamente")
                    
                    siguiente = request.args.get('next')
                    print(f"LOGIN DEBUG: Next URL: {siguiente}")
                    
                    if siguiente and siguiente.startswith('/'):
                        print(f"LOGIN DEBUG: Redirigiendo a: {siguiente}")
                        return redirect(siguiente)
                    
                    print("LOGIN DEBUG: Redirigiendo a index...")
                    flash(f'¡Bienvenido {usuario.nombre_usuario}!', 'success')
                    return redirect(url_for('index'))
                else:
                    print("LOGIN DEBUG: Contraseña incorrecta")
            else:
                print("LOGIN DEBUG: Usuario no encontrado")
                
        except Exception as e:
            print(f"LOGIN ERROR: Error durante login: {e}")
            import traceback
            traceback.print_exc()
            flash(f'Error en el sistema: {str(e)}', 'error')
            return render_template('login.html', form=form)
        
        flash('Usuario/email o contraseña incorrectos', 'error')
    
    return render_template('login.html', form=form)

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegisterForm()
    
    # Inicializar opciones del campo rol para evitar TypeError
    # En registro público solo permitimos rol Candidato (id=4)
    form.rol.choices = [(4, 'Candidato')]
    form.rol.data = 4  # Forzar el valor por defecto
    
    if form.validate_on_submit():
        # Validación adicional: verificar que las contraseñas coincidan
        if form.password.data != form.password_confirm.data:
            flash('Las contraseñas no coinciden. Por favor verifica e intenta nuevamente.', 'error')
            return render_template('registro.html', form=form)
        
        try:
            # 🔒 SEGURIDAD: Forzar siempre rol=Candidato (id=4) en registro público
            # Ignorar cualquier valor manipulado del formulario
            rol_id_forzado = 4  # 4 = Candidato
            
            # Validación adicional de seguridad
            if hasattr(form, 'rol') and form.rol.data != 4:
                # Log del intento de manipulación (en producción usar logger)
                import logging
                logging.warning(f"Intento de manipulación de rol detectado: {form.rol.data}")
                flash('Error en el registro. Por favor intenta nuevamente.', 'error')
                return redirect(url_for('registro'))
            
            # Generar nombre_usuario automáticamente desde el email
            nombre_usuario = form.email.data.split('@')[0]
            
            # Si el nombre_usuario ya existe, agregar un sufijo
            contador = 1
            nombre_usuario_original = nombre_usuario
            with db.get_connection() as conn:
                cursor = conn.cursor()
                while True:
                    cursor.execute('SELECT id_usuario FROM usuarios WHERE nombre_usuario = %s', (nombre_usuario,))
                    if not cursor.fetchone():
                        break
                    nombre_usuario = f"{nombre_usuario_original}{contador}"
                    contador += 1
            
            usuario = Usuario(
                nombre_usuario=nombre_usuario,
                email=form.email.data,
                rol_id=rol_id_forzado,  # Siempre forzado a Candidato
                activo=True
            )
            usuario.set_password(form.password.data)
            usuario.save()
            
            flash('¡Cuenta creada exitosamente! Por favor inicia sesión', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Error al crear la cuenta: {str(e)}', 'error')
    else:
        # Si el formulario no se validó, mostrar errores específicos
        print(f"DEBUG: Formulario NO validado. Errores: {form.errors}")
        for field_name, field_errors in form.errors.items():
            for error in field_errors:
                print(f"DEBUG: Error en {field_name}: {error}")
                flash(f'Error en {field_name}: {error}', 'error')
    
    return render_template('registro.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada correctamente', 'info')
    return redirect(url_for('login'))

@app.route('/')
def index():
    print("INDEX DEBUG: Entrando a ruta index")
    
    if not current_user.is_authenticated:
        print("INDEX DEBUG: Usuario no autenticado, redirigiendo a login")
        return redirect(url_for('login'))
    
    print(f"INDEX DEBUG: Usuario autenticado: {current_user.nombre_usuario}, Rol: {current_user.rol_nombre}")
    
    # Dashboard diferenciado por rol
    if current_user.rol_nombre == 'candidato':
        print("INDEX DEBUG: Es candidato, verificando perfil...")
        # Verificar si el candidato tiene perfil completo
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT cedula, nombre, apellido FROM candidatos WHERE email = %s LIMIT 1', (current_user.email,))
                candidato_row = cursor.fetchone()
            
            if not candidato_row:
                print("INDEX DEBUG: Candidato sin perfil, redirigiendo a completar perfil")
                flash('Debes completar tu perfil de candidato para continuar', 'warning')
                return redirect(url_for('completar_perfil_candidato'))
            
            # Candidatos ven cargos disponibles
            print("INDEX DEBUG: Obteniendo cargos activos...")
            cargos = Cargo.get_all(estado='Activo')
            print(f"INDEX DEBUG: Cargos encontrados: {len(cargos)}")
            
            # Extraer nombre y apellido del candidato
            candidato_nombre = candidato_row.get('nombre', '') if isinstance(candidato_row, dict) else candidato_row[1] if len(candidato_row) > 1 else ''
            candidato_apellido = candidato_row.get('apellido', '') if isinstance(candidato_row, dict) else candidato_row[2] if len(candidato_row) > 2 else ''
            candidato_nombre_completo = f"{candidato_nombre} {candidato_apellido}".strip()
            
            return render_template('candidato/dashboard.html', cargos=cargos, candidato_nombre=candidato_nombre_completo)
        except Exception as e:
            print(f"INDEX ERROR: Error en dashboard candidato: {e}")
            import traceback
            traceback.print_exc()
            flash(f'Error al cargar dashboard: {str(e)}', 'error')
            return render_template('candidato/dashboard.html', cargos=[], candidato_nombre=current_user.nombre_usuario)
    else:
        print("INDEX DEBUG: Es admin/reclutador/gerente, obteniendo estadísticas...")
        # Administrador, reclutador y gerente ven estadísticas
        try:
            print("INDEX DEBUG: Llamando a EstadisticasRRHH.get_dashboard_stats()...")
            stats = EstadisticasRRHH.get_dashboard_stats()
            print(f"INDEX DEBUG: Estadísticas obtenidas: {stats}")
            return render_template('index.html', stats=stats)
        except Exception as e:
            print(f"INDEX ERROR: Error en EstadisticasRRHH.get_dashboard_stats(): {e}")
            import traceback
            traceback.print_exc()
            # Estadísticas por defecto si hay error
            stats = {
                'total_candidatos': 0,
                'candidatos_activos': 0,
                'total_postulaciones': 0,
                'postulaciones_pendientes': 0,
                'total_cargos': 0,
                'cargos_activos': 0
            }
            flash(f'Error al cargar estadísticas: {str(e)}', 'error')
            return render_template('index.html', stats=stats)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/completar-perfil', methods=['GET', 'POST'])
@login_required
@require_role(['candidato'])
def completar_perfil_candidato():
    """Formulario unificado para que un candidato complete su perfil"""
    form = CandidatoRegistroForm()
    
    # Crear formularios de referencias y experiencias (3 cada uno)
    referencias_forms = [ReferenciaForm(prefix=f'ref_{i}') for i in range(3)]
    experiencias_forms = [ExperienciaForm(prefix=f'exp_{i}') for i in range(3)]
    
    # Verificar si el usuario ya tiene un perfil
    candidato = None
    referencias = []
    experiencias = []
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM candidatos WHERE email = %s', (current_user.email,))
        resultado = cursor.fetchone()
        if resultado:
            candidato = Candidato.from_row(resultado)
            
            # Cargar referencias existentes
            cursor.execute('''
                SELECT id_referencia, nombre, telefono, relacion, descripcion 
                FROM referencias_personales 
                WHERE cedula = %s 
                ORDER BY id_referencia
            ''', (candidato.cedula,))
            referencias = [Referencia.from_row(r) for r in cursor.fetchall()]
            
            # Cargar experiencias existentes
            cursor.execute('''
                SELECT id_experiencia, empresa, cargo, descripcion, fecha_inicio, fecha_fin, actual
                FROM experiencias 
                WHERE cedula = %s 
                ORDER BY id_experiencia
            ''', (candidato.cedula,))
            experiencias = [Experiencia.from_row(r) for r in cursor.fetchall()]
            
            # Pre-llenar el formulario con los datos del candidato
            if candidato and request.method == 'GET':
                form.cedula.data = candidato.cedula
                form.nombre.data = candidato.nombre
                form.apellido.data = candidato.apellido
                form.telefono.data = candidato.telefono
                form.direccion_domicilio.data = candidato.direccion_domicilio
                form.resumen.data = candidato.resumen
                form.habilidades.data = ', '.join(candidato.habilidades) if candidato.habilidades else ''
                form.experiencia_anos.data = candidato.experiencia_anos
                form.nivel_educativo.data = candidato.nivel_educativo
                form.disponibilidad.data = candidato.disponibilidad
                form.salario_esperado.data = candidato.salario_esperado
    
    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                # Crear o actualizar candidato
                if not candidato:
                    candidato = Candidato(
                        cedula=form.cedula.data,
                        nombre=form.nombre.data,
                        apellido=form.apellido.data,
                        email=current_user.email,
                        telefono=form.telefono.data,
                        resumen=form.resumen.data,
                        habilidades=[h.strip() for h in form.habilidades.data.split(',')] if form.habilidades.data else [],
                        experiencia_anos=form.experiencia_anos.data or 0,
                        nivel_educativo=form.nivel_educativo.data,
                        direccion_domicilio=form.direccion_domicilio.data,
                        disponibilidad=form.disponibilidad.data,
                        salario_esperado=form.salario_esperado.data or 0.0
                    )
                else:
                    # Actualizar datos existentes
                    candidato.nombre = form.nombre.data
                    candidato.apellido = form.apellido.data
                    candidato.telefono = form.telefono.data
                    candidato.resumen = form.resumen.data
                    candidato.habilidades = [h.strip() for h in form.habilidades.data.split(',')] if form.habilidades.data else []
                    candidato.experiencia_anos = form.experiencia_anos.data or 0
                    candidato.nivel_educativo = form.nivel_educativo.data
                    candidato.direccion_domicilio = form.direccion_domicilio.data
                    candidato.disponibilidad = form.disponibilidad.data
                    candidato.salario_esperado = form.salario_esperado.data or 0.0
                
                candidato.save()
                
                # Eliminar referencias y experiencias antiguas para reemplazarlas
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM referencias_personales WHERE cedula = %s', (candidato.cedula,))
                    cursor.execute('DELETE FROM experiencias WHERE cedula = %s', (candidato.cedula,))
                
                # Guardar referencias
                for i in range(3):
                    if request.form.get(f'ref_{i}-nombre_completo'):
                        ref = Referencia(
                            cedula=candidato.cedula,
                            nombre=request.form.get(f'ref_{i}-nombre_completo'),
                            telefono=request.form.get(f'ref_{i}-telefono'),
                            relacion=request.form.get(f'ref_{i}-tipo_referencia', 'Amigo'),
                            descripcion=request.form.get(f'ref_{i}-contestacion', 'No aplica')
                        )
                        ref.save()
                
                # Guardar experiencias
                for i in range(3):
                    if request.form.get(f'exp_{i}-empresa'):
                        fecha_inicio = request.form.get(f'exp_{i}-fecha_inicio')
                        fecha_fin = request.form.get(f'exp_{i}-fecha_fin') or None
                        
                        exp = Experiencia(
                            cedula=candidato.cedula,
                            empresa=request.form.get(f'exp_{i}-empresa'),
                            cargo=request.form.get(f'exp_{i}-cargo'),
                            fecha_inicio=datetime.strptime(fecha_inicio, '%Y-%m-%d').date() if fecha_inicio else None,
                            fecha_fin=datetime.strptime(fecha_fin, '%Y-%m-%d').date() if fecha_fin else None,
                            actual=request.form.get(f'exp_{i}-actual') == 'y',
                            descripcion=request.form.get(f'exp_{i}-descripcion', '')
                        )
                        exp.save()
                
                # Manejar archivo de currículum
                if 'curriculum' in request.files:
                    curriculum_file = request.files['curriculum']
                    if curriculum_file and curriculum_file.filename != '':
                        # Validar archivo
                        if not curriculum_file.filename.lower().endswith('.pdf'):
                            flash('Solo se permiten archivos PDF', 'error')
                            return render_template('candidato/completar_perfil.html', 
                                                 form=form, 
                                                 referencias_forms=referencias_forms,
                                                 experiencias_forms=experiencias_forms,
                                                 candidato=candidato,
                                                 referencias=referencias,
                                                 experiencias=experiencias,
                                                 titulo='Completar Perfil')
                        
                        # Validar tamaño (máximo 5 MB)
                        MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
                        curriculum_file.seek(0, os.SEEK_END)
                        file_size = curriculum_file.tell()
                        if file_size > MAX_FILE_SIZE:
                            flash('El archivo debe pesar menos de 5 MB', 'error')
                            return render_template('candidato/completar_perfil.html', 
                                                 form=form, 
                                                 referencias_forms=referencias_forms,
                                                 experiencias_forms=experiencias_forms,
                                                 candidato=candidato,
                                                 referencias=referencias,
                                                 experiencias=experiencias,
                                                 titulo='Completar Perfil')
                        curriculum_file.seek(0)
                        
                        # Guardar archivo
                        upload_dir = os.path.join(os.path.dirname(__file__), 'uploads', 'curriculum')
                        os.makedirs(upload_dir, exist_ok=True)
                        filename = secure_filename(f"{candidato.cedula}_{candidato.nombre}_{candidato.apellido}.pdf")
                        curriculum_path = os.path.join(upload_dir, filename)
                        curriculum_file.save(curriculum_path)
                        
                        # TEMPORALMENTE DESACTIVADO - Subida de CV
                        # Guardar registro del documento en la base de datos
                        # try:
                        #     with db.get_connection() as conn:
                        #         cursor = conn.cursor()
                        #         print(f"Intentando insertar documento: {filename}")
                        #         cursor.execute('''
                        #             INSERT INTO documentos (id_postulacion, tipo_documento, nombre_archivo, ruta_archivo, tamano_archivo)
                        #             VALUES (%s, %s, %s, %s, %s)
                        #         ''', (None, 'curriculum', filename, f'uploads/curriculum/{filename}', os.path.getsize(curriculum_path)))
                        #         conn.commit()
                        #         print("Documento insertado correctamente")
                        # except Exception as doc_error:
                        #     print(f"Error al insertar documento: {str(doc_error)}")
                        #     flash(f'Error al guardar el registro del documento: {str(doc_error)}', 'error')
                        print("Subida de CV temporalmente desactivada")
                
                flash(' Perfil de candidato completado exitosamente', 'success')
                return redirect(url_for('index'))
                
            except Exception as e:
                flash(f'Error al guardar: {str(e)}', 'error')
        else:
            # Mostrar errores de validación si existen
            for field_name, field_errors in form.errors.items():
                for error in field_errors:
                    flash(f'Error en {field_name}: {error}', 'error')
    
    return render_template('candidato/completar_perfil.html', 
                         form=form, 
                         referencias_forms=referencias_forms,
                         experiencias_forms=experiencias_forms,
                         candidato=candidato,
                         referencias=referencias,
                         experiencias=experiencias,
                         titulo='Completar Perfil')

# ============ RUTAS CANDIDATOS - Ver cargos y postulase ============
@app.route('/cargos-disponibles')
@login_required
@require_role(['candidato'])
def cargos_candidato():
    """Muestra cargos disponibles para que los candidatos se postlen"""
    # Verificar si el candidato tiene perfil completo
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT cedula FROM candidatos WHERE email = %s LIMIT 1', (current_user.email,))
        result = cursor.fetchone()
    
    if not result:
        flash('Debes completar tu perfil de candidato para ver las vacantes disponibles', 'warning')
        return redirect(url_for('completar_perfil_candidato'))
    
    cargos = Cargo.get_all(estado='Activo')
    return render_template('candidato/cargos_disponibles.html', cargos=cargos)

@app.route('/mis-postulaciones')
@login_required
@require_role(['candidato'])
def mis_postulaciones():
    """Muestra postulaciones del candidato actual"""
    # Obtenemos la cedula del candidato desde el email del usuario
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT cedula FROM candidatos WHERE email = %s LIMIT 1
        ''', (current_user.email,))
        result = cursor.fetchone()
    
    if not result:
        flash('Debes completar tu perfil de candidato para ver tus postulaciones', 'warning')
        return redirect(url_for('completar_perfil_candidato'))
    
    cedula_candidato = result['cedula']
    
    # Obtenemos todas las postulaciones del candidato
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.*, c.nombre as cargo_nombre, c.departamento, ce.nombre, ce.apellido
            FROM postulaciones p
            JOIN cargos c ON p.id_cargo = c.id_cargo
            JOIN candidatos ce ON p.cedula = ce.cedula
            WHERE p.cedula = %s
            ORDER BY p.fecha_postulacion DESC
        ''', (cedula_candidato,))
        postulaciones = cursor.fetchall()
    
    return render_template('candidato/mis_postulaciones.html', postulaciones=postulaciones)

@app.route('/postular/<int:cargo_id>', methods=['GET', 'POST'])
@login_required
@require_role(['candidato'])
def postular_a_cargo(cargo_id):
    """Formulario para que el candidato se postule a una vacante"""
    cargo = Cargo.get_by_id(cargo_id)
    if not cargo or cargo.estado != 'Activo':
        flash('La vacante no está disponible', 'error')
        return redirect(url_for('cargos_candidato'))
    
    # Obtener datos del candidato
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM candidatos WHERE email = %s LIMIT 1
        ''', (current_user.email,))
        candidato = cursor.fetchone()
    
    if not candidato:
        flash('Debes completar tu perfil de candidato para postularte a vacantes', 'warning')
        return redirect(url_for('completar_perfil_candidato'))
    
    if request.method == 'POST':
        # Verificar si ya está postulado
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id_postulacion FROM postulaciones 
                WHERE cedula = %s AND id_cargo = %s
            ''', (candidato['cedula'], cargo_id))
            existe = cursor.fetchone()
        
        if existe:
            flash('Ya te has postulado a esta vacante previamente', 'warning')
            return redirect(url_for('cargos_candidato'))
        
        # Insertar postulación
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO postulaciones (cedula, id_cargo, estado, fuente_reclutamiento, fecha_postulacion)
                VALUES (%s, %s, %s, %s, NOW())
            ''', (candidato['cedula'], cargo_id, 'Recibido', 'Web corporativa'))
            conn.commit()
        
        flash(f'¡Postulación enviada exitosamente a {cargo.nombre}!', 'success')
        return redirect(url_for('mis_postulaciones'))
    
    return render_template('candidato/postular.html', cargo=cargo, candidato=candidato)

# ============ RUTAS CARGOS ============
@app.route('/cargos')
@login_required
@require_role(['admin', 'reclutador', 'gerente'])
def lista_cargos():
    estado = request.args.get('estado')
    cargos = Cargo.get_all(estado=estado)
    return render_template('cargos/lista.html', cargos=cargos, estado_filtro=estado)

@app.route('/cargos/nuevo', methods=['GET', 'POST'])
@login_required
@require_role(['admin', 'reclutador', 'gerente'])
def nuevo_cargo():
    print("CARGO DEBUG: Entrando a nuevo_cargo()")
    form = CargoForm()
    print(f"CARGO DEBUG: Formulario creado, validate_on_submit: {form.validate_on_submit()}")
    
    if form.validate_on_submit():
        try:
            print(f"CARGO DEBUG: Datos del formulario: nombre={form.nombre.data}, depto={form.departamento.data}")
            cargo = Cargo(
                nombre=form.nombre.data,
                descripcion=form.descripcion.data,
                departamento=form.departamento.data,
                salario_minimo=form.salario_minimo.data,
                salario_maximo=form.salario_maximo.data,
                tipo_contrato=form.tipo_contrato.data,
                id_sucursal=form.id_sucursal.data,
                estado=form.estado.data,
                fecha_cierre=form.fecha_cierre.data
            )
            print(f"CARGO DEBUG: Cargo creado, llamando save()...")
            cargo.save()
            print(f"CARGO DEBUG: Cargo guardado exitosamente")
            flash('✅ Vacante creada exitosamente', 'success')
            return redirect(url_for('lista_cargos'))
        except Exception as e:
            print(f"CARGO ERROR: Error al crear cargo: {e}")
            import traceback
            traceback.print_exc()
            flash(f'❌ Error al crear vacante: {str(e)}', 'error')
            return render_template('cargos/formulario.html', form=form, titulo='Nueva Vacante')
    else:
        if request.method == 'POST':
            print(f"CARGO DEBUG: Formulario no validado. Errores: {form.errors}")
            for field_name, field_errors in form.errors.items():
                for error in field_errors:
                    flash(f'Error en {field_name}: {error}', 'error')
    
    return render_template('cargos/formulario.html', form=form, titulo='Nueva Vacante')

@app.route('/cargos/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@require_role(['admin', 'reclutador', 'gerente'])
def editar_cargo(id):
    cargo = Cargo.get_by_id(id)
    if not cargo:
        flash('Vacante no encontrada', 'error')
        return redirect(url_for('lista_cargos'))
    
    if cargo.fecha_cierre and isinstance(cargo.fecha_cierre, str):
        try:
            cargo.fecha_cierre = datetime.strptime(cargo.fecha_cierre, '%Y-%m-%d').date()
        except ValueError:
            cargo.fecha_cierre = None
    
    form = CargoForm(obj=cargo)
    if form.validate_on_submit():
        cargo.nombre = form.nombre.data
        cargo.descripcion = form.descripcion.data
        cargo.departamento = form.departamento.data
        cargo.salario_minimo = form.salario_minimo.data
        cargo.salario_maximo = form.salario_maximo.data
        cargo.tipo_contrato = form.tipo_contrato.data
        cargo.id_sucursal = form.id_sucursal.data
        cargo.estado = form.estado.data
        cargo.fecha_cierre = form.fecha_cierre.data
        cargo.save()
        flash('✅ Vacante actualizada exitosamente', 'success')
        return redirect(url_for('lista_cargos'))
    
    return render_template('cargos/formulario.html', form=form, titulo='Editar Vacante', cargo=cargo)

@app.route('/cargos/<int:id>/desactivar', methods=['POST'])
@login_required
@require_role(['admin', 'reclutador', 'gerente'])
def desactivar_cargo(id):
    """Desactiva un cargo (cambia estado a Inactivo)"""
    cargo = Cargo.get_by_id(id)
    if cargo:
        cargo.estado = 'Inactivo'
        cargo.save()
        flash('🗑️ Vacante desactivada', 'info')
    return redirect(url_for('lista_cargos'))

@app.route('/cargos/<int:id>/activar', methods=['POST'])
@login_required
@require_role(['admin', 'reclutador', 'gerente'])
def activar_cargo(id):
    """Activa un cargo (cambia estado a Activo)"""
    cargo = Cargo.get_by_id(id)
    if cargo:
        cargo.estado = 'Activo'
        cargo.save()
        flash('✅ Vacante activada', 'success')
    return redirect(url_for('lista_cargos'))

@app.route('/cargos/<int:id>/eliminar', methods=['POST'])
@login_required
@require_role(['admin'])  # SOLO ADMIN puede eliminar completamente
def eliminar_cargo(id):
    """Elimina completamente un cargo de la base de datos (solo admin)"""
    cargo = Cargo.get_by_id(id)
    if cargo:
        try:
            # Verificar si hay postulaciones asociadas
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) as count FROM postulaciones WHERE cargo_id = %s', (cargo.id_cargo,))
                result = cursor.fetchone()
                
                if result['count'] > 0:
                    flash(f'❌ No se puede eliminar la vacante porque tiene {result["count"]} postulaciones asociadas', 'error')
                    return redirect(url_for('lista_cargos'))
                
                # Eliminar el cargo
                cargo.delete()
                flash('🗑️ Vacante eliminada permanentemente de la base de datos', 'success')
        except Exception as e:
            flash(f'❌ Error al eliminar vacante: {str(e)}', 'error')
    return redirect(url_for('lista_cargos'))

# ============ RUTAS CANDIDATOS ============
@app.route('/candidatos')
@login_required
@require_role(['admin', 'reclutador', 'gerente'])
def lista_candidatos():
    form_busqueda = BusquedaCandidatoForm(request.args)
    activo = request.args.get('activo', '1') == '1'
    page = request.args.get('page', 1, type=int)
    per_page = 5
    busqueda = request.args.get('busqueda', '').strip() #capturar busqueda
    disponibilidad = request.args.get('disponibilidad', '').strip() #
    
    paginated_data = Candidato.get_paginated(
        page=page, 
        per_page=per_page, 
        activo=activo, 
        busqueda=busqueda, 
        disponibilidad=disponibilidad
    )
    
    return render_template('candidatos/lista.html', 
                         **paginated_data,
                         form_busqueda=form_busqueda,
                         activo=activo,
                         busqueda=busqueda,
                         disponibilidad=disponibilidad)

@app.route('/candidato/actualizar-perfil', methods=['GET', 'POST'])
@login_required
@require_role(['candidato'])
def actualizar_perfil_candidato():
    """Permite al candidato actualizar su perfil completo"""
    # Obtener candidato por email del usuario actual
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM candidatos WHERE email = %s', (current_user.email,))
        result = cursor.fetchone()
    
    if not result:
        flash('No se encontró tu perfil de candidato', 'error')
        return redirect(url_for('index'))
    
    candidato = Candidato.from_row(result)
    
    # Cargar referencias y experiencias existentes
    referencias = []
    experiencias = []
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id_referencia, nombre, telefono, relacion, descripcion 
            FROM referencias_personales 
            WHERE cedula = %s 
            ORDER BY id_referencia
        ''', (candidato.cedula,))
        referencias = [Referencia.from_row(r) for r in cursor.fetchall()]
        
        cursor.execute('''
            SELECT id_experiencia, empresa, cargo, descripcion, fecha_inicio, fecha_fin, actual
            FROM experiencias 
            WHERE cedula = %s 
            ORDER BY id_experiencia
        ''', (candidato.cedula,))
        experiencias = [Experiencia.from_row(r) for r in cursor.fetchall()]
    
    form = CandidatoForm(obj=candidato)
    
    # Pre-llenar el formulario con los datos del candidato
    if request.method == 'GET':
        form.cedula.data = candidato.cedula
        form.nombre.data = candidato.nombre
        form.apellido.data = candidato.apellido
        form.email.data = candidato.email
        form.telefono.data = candidato.telefono
        form.resumen.data = candidato.resumen
        form.habilidades.data = ', '.join(candidato.habilidades) if candidato.habilidades else ''
        form.nivel_educativo.data = candidato.nivel_educativo
        form.direccion_domicilio.data = candidato.direccion_domicilio
        form.disponibilidad.data = candidato.disponibilidad
        form.salario_esperado.data = candidato.salario_esperado
    
    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                # Actualizar datos del candidato
                candidato.nombre = form.nombre.data
                candidato.apellido = form.apellido.data
                candidato.telefono = form.telefono.data
                candidato.resumen = form.resumen.data
                candidato.habilidades = [h.strip() for h in form.habilidades.data.split(',')] if form.habilidades.data else []
                candidato.nivel_educativo = form.nivel_educativo.data
                candidato.direccion_domicilio = form.direccion_domicilio.data
                candidato.disponibilidad = form.disponibilidad.data
                candidato.salario_esperado = form.salario_esperado.data or 0.0
                
                candidato.save()
                
                # Eliminar referencias y experiencias antiguas para reemplazarlas
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM referencias_personales WHERE cedula = %s', (candidato.cedula,))
                    cursor.execute('DELETE FROM experiencias WHERE cedula = %s', (candidato.cedula,))
                
                # Guardar referencias
                for i in range(3):
                    if request.form.get(f'ref_{i}-nombre_completo'):
                        ref = Referencia(
                            cedula=candidato.cedula,
                            nombre=request.form.get(f'ref_{i}-nombre_completo'),
                            telefono=request.form.get(f'ref_{i}-telefono'),
                            relacion=request.form.get(f'ref_{i}-tipo_referencia', 'Amigo'),
                            descripcion=request.form.get(f'ref_{i}-contestacion', 'No aplica')
                        )
                        ref.save()
                
                # Guardar experiencias
                for i in range(3):
                    if request.form.get(f'exp_{i}-empresa'):
                        fecha_inicio = request.form.get(f'exp_{i}-fecha_inicio')
                        fecha_fin = request.form.get(f'exp_{i}-fecha_fin') or None
                        
                        exp = Experiencia(
                            cedula=candidato.cedula,
                            empresa=request.form.get(f'exp_{i}-empresa'),
                            cargo=request.form.get(f'exp_{i}-cargo'),
                            fecha_inicio=datetime.strptime(fecha_inicio, '%Y-%m-%d').date() if fecha_inicio else None,
                            fecha_fin=datetime.strptime(fecha_fin, '%Y-%m-%d').date() if fecha_fin else None,
                            actual=request.form.get(f'exp_{i}-actual') == 'y',
                            descripcion=request.form.get(f'exp_{i}-descripcion', '')
                        )
                        exp.save()
                
                flash('✅ Perfil actualizado exitosamente', 'success')
                return redirect(url_for('cargos_candidato'))
                
            except Exception as e:
                flash(f'Error al actualizar: {str(e)}', 'error')
    
    return render_template('candidato/actualizar_perfil.html', 
                         form=form, 
                         candidato=candidato,
                         referencias=referencias,
                         experiencias=experiencias,
                         titulo='Actualizar Mi Perfil')

@app.route('/candidatos/<string:cedula>')
@login_required
@require_role(['admin', 'reclutador', 'gerente'])
def detalle_candidato(cedula):
    candidato = Candidato.get_by_cedula(cedula)
    if not candidato:
        flash('Candidato no encontrado', 'error')
        return redirect(url_for('lista_candidatos'))
    
    # Cargar postulaciones del candidato
    postulaciones = Postulacion.get_por_candidato(cedula)
    
    return render_template('candidatos/detalle.html', candidato=candidato, postulaciones=postulaciones)

@app.route('/candidatos/nuevo', methods=['GET', 'POST'])
@login_required
@require_role(['admin', 'reclutador', 'gerente'])
def nuevo_candidato():
    form = CandidatoForm()
    
    # Crear formularios de referencias y experiencias (3 cada uno)
    referencias_forms = [ReferenciaForm(prefix=f'ref_{i}') for i in range(3)]
    experiencias_forms = [ExperienciaForm(prefix=f'exp_{i}') for i in range(3)]
    
    if form.validate_on_submit():
        try:
            # Crear candidato
            candidato = Candidato(
                cedula=form.cedula.data,
                nombre=form.nombre.data,
                apellido=form.apellido.data,
                email=form.email.data,
                telefono=form.telefono.data,
                resumen=form.resumen.data,
                habilidades=[h.strip() for h in form.habilidades.data.split(',')] if form.habilidades.data else [],
                experiencia_anos=form.experiencia_anos.data or 0,
                nivel_educativo=form.nivel_educativo.data,
                direccion_domicilio=form.direccion_domicilio.data,
                disponibilidad=form.disponibilidad.data,
                salario_esperado=form.salario_esperado.data or 0.0,
                cargo_id=form.cargo_id.data
            )
            candidato.save()
            
            # Guardar referencias
            for i in range(3):
                if request.form.get(f'ref_{i}-nombre_completo'):
                    ref = Referencia(
                        cedula=form.cedula.data,
                        nombre=request.form.get(f'ref_{i}-nombre_completo'),
                        telefono=request.form.get(f'ref_{i}-telefono'),
                        relacion=request.form.get(f'ref_{i}-tipo_referencia', 'Amigo'),
                        descripcion=request.form.get(f'ref_{i}-contestacion', 'No aplica')
                    )
                    ref.save()
            
            # Guardar experiencias
            for i in range(3):
                if request.form.get(f'exp_{i}-empresa'):
                    fecha_inicio = request.form.get(f'exp_{i}-fecha_inicio')
                    fecha_fin = request.form.get(f'exp_{i}-fecha_fin') or None
                    
                    exp = Experiencia(
                        cedula=form.cedula.data,
                        empresa=request.form.get(f'exp_{i}-empresa'),
                        cargo=request.form.get(f'exp_{i}-cargo'),
                        fecha_inicio=datetime.strptime(fecha_inicio, '%Y-%m-%d').date() if fecha_inicio else None,
                        fecha_fin=datetime.strptime(fecha_fin, '%Y-%m-%d').date() if fecha_fin else None,
                        actual=request.form.get(f'exp_{i}-actual') == 'y',
                        descripcion=request.form.get(f'exp_{i}-descripcion', '')
                    )
                    exp.save()
            
            # Manejar archivo de currículum
            if 'curriculum' in request.files:
                curriculum_file = request.files['curriculum']
                if curriculum_file and curriculum_file.filename != '':
                    # Validar archivo
                    if not curriculum_file.filename.lower().endswith('.pdf'):
                        flash('Solo se permiten archivos PDF', 'error')
                        return render_template('candidatos/formulario.html', 
                                             form=form, 
                                             referencias_forms=referencias_forms,
                                             experiencias_forms=experiencias_forms,
                                             titulo='Nuevo Candidato')
                    
                    # Validar tamaño (máximo 5 MB)
                    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
                    curriculum_file.seek(0, os.SEEK_END)
                    file_size = curriculum_file.tell()
                    if file_size > MAX_FILE_SIZE:
                        flash('El archivo debe pesar menos de 5 MB', 'error')
                        return render_template('candidatos/formulario.html', 
                                             form=form, 
                                             referencias_forms=referencias_forms,
                                             experiencias_forms=experiencias_forms,
                                             titulo='Nuevo Candidato')
                    curriculum_file.seek(0)
                    
                    # Guardar archivo
                    upload_dir = os.path.join(os.path.dirname(__file__), 'uploads', 'curriculum')
                    os.makedirs(upload_dir, exist_ok=True)
                    filename = secure_filename(f"{candidato.cedula}_{candidato.nombre}_{candidato.apellido}.pdf")
                    curriculum_path = os.path.join(upload_dir, filename)
                    curriculum_file.save(curriculum_path)
                    
                    # TEMPORALMENTE DESACTIVADO - Subida de CV
                    # Guardar registro del documento en la base de datos
                    # try:
                    #     with db.get_connection() as conn:
                    #         cursor = conn.cursor()
                    #         print(f"Intentando insertar documento: {filename}")
                    #         cursor.execute('''
                    #             INSERT INTO documentos (id_postulacion, tipo_documento, nombre_archivo, ruta_archivo, tamano_archivo)
                    #             VALUES (%s, %s, %s, %s, %s)
                    #         ''', (None, 'curriculum', filename, f'uploads/curriculum/{filename}', os.path.getsize(curriculum_path)))
                    #         conn.commit()
                    #         print("Documento insertado correctamente")
                    # except Exception as doc_error:
                    #     print(f"Error al insertar documento: {str(doc_error)}")
                    #     flash(f'Error al guardar el registro del documento: {str(doc_error)}', 'error')
                    print("Subida de CV temporalmente desactivada")
            
            # Crear postulación automática
            postulacion = Postulacion(
                candidato_cedula=form.cedula.data,
                cargo_id=form.cargo_id.data,
                estado='Recibido',
                fuente_reclutamiento='Web corporativa'
            )
            postulacion.save()
            
            flash('✅ Candidato registrado exitosamente', 'success')
            return redirect(url_for('lista_candidatos'))
            
        except Exception as e:
            flash(f'Error al guardar: {str(e)}', 'error')
    
    return render_template('candidatos/formulario.html', 
                         form=form, 
                         referencias_forms=referencias_forms,
                         experiencias_forms=experiencias_forms,
                         titulo='Nuevo Candidato')

@app.route('/candidatos/<string:cedula>/editar', methods=['GET', 'POST'])
@login_required
@require_role(['admin', 'reclutador'])
def editar_candidato(cedula):
    candidato = Candidato.get_by_cedula(cedula)
    if not candidato:
        flash('Candidato no encontrado', 'error')
        return redirect(url_for('lista_candidatos'))
    
    # Cargar referencias y experiencias existentes
    referencias = []
    experiencias = []
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id_referencia, nombre, telefono, relacion, descripcion 
            FROM referencias_personales 
            WHERE cedula = %s 
            ORDER BY id_referencia
        ''', (candidato.cedula,))
        referencias = [Referencia.from_row(r) for r in cursor.fetchall()]
        
        cursor.execute('''
            SELECT id_experiencia, empresa, cargo, descripcion, fecha_inicio, fecha_fin, actual
            FROM experiencias 
            WHERE cedula = %s 
            ORDER BY id_experiencia
        ''', (candidato.cedula,))
        experiencias = [Experiencia.from_row(r) for r in cursor.fetchall()]
    
    # Crear formularios de referencias y experiencias (3 cada uno)
    referencias_forms = [ReferenciaForm(prefix=f'ref_{i}') for i in range(3)]
    experiencias_forms = [ExperienciaForm(prefix=f'exp_{i}') for i in range(3)]
    
    form = CandidatoForm(obj=candidato)
    
    if request.method == 'POST':
        if form.validate_on_submit():
            # Actualizar datos del candidato
            candidato.nombre = form.nombre.data
            candidato.apellido = form.apellido.data
            candidato.email = form.email.data
            candidato.telefono = form.telefono.data
            candidato.resumen = form.resumen.data
            candidato.habilidades = [h.strip() for h in form.habilidades.data.split(',')] if form.habilidades.data else []
            candidato.experiencia_anos = form.experiencia_anos.data or 0
            candidato.nivel_educativo = form.nivel_educativo.data
            candidato.direccion_domicilio = form.direccion_domicilio.data
            candidato.disponibilidad = form.disponibilidad.data
            candidato.salario_esperado = form.salario_esperado.data or 0.0
            candidato.cargo_id = form.cargo_id.data
            
            candidato.save()
            
            # Eliminar referencias y experiencias antiguas para reemplazarlas
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM referencias_personales WHERE cedula = %s', (candidato.cedula,))
                cursor.execute('DELETE FROM experiencias WHERE cedula = %s', (candidato.cedula,))
            
            # Guardar referencias
            for i in range(3):
                if request.form.get(f'ref_{i}-nombre_completo'):
                    ref = Referencia(
                        cedula=candidato.cedula,
                        nombre=request.form.get(f'ref_{i}-nombre_completo'),
                        telefono=request.form.get(f'ref_{i}-telefono'),
                        relacion=request.form.get(f'ref_{i}-tipo_referencia', 'Amigo'),
                        descripcion=request.form.get(f'ref_{i}-contestacion', 'No aplica')
                    )
                    ref.save()
            
            # Guardar experiencias
            for i in range(3):
                if request.form.get(f'exp_{i}-empresa'):
                    fecha_inicio = request.form.get(f'exp_{i}-fecha_inicio')
                    fecha_fin = request.form.get(f'exp_{i}-fecha_fin') or None
                    
                    exp = Experiencia(
                        cedula=candidato.cedula,
                        empresa=request.form.get(f'exp_{i}-empresa'),
                        cargo=request.form.get(f'exp_{i}-cargo'),
                        fecha_inicio=datetime.strptime(fecha_inicio, '%Y-%m-%d').date() if fecha_inicio else None,
                        fecha_fin=datetime.strptime(fecha_fin, '%Y-%m-%d').date() if fecha_fin else None,
                        actual=request.form.get(f'exp_{i}-actual') == 'y',
                        descripcion=request.form.get(f'exp_{i}-descripcion', '')
                    )
                    exp.save()
            
            flash('✅ Candidato actualizado exitosamente', 'success')
            return redirect(url_for('detalle_candidato', cedula=cedula))
    
    return render_template('candidatos/formulario.html', 
                         form=form, 
                         referencias_forms=referencias_forms,
                         experiencias_forms=experiencias_forms,
                         candidato=candidato,
                         referencias=referencias,
                         experiencias=experiencias,
                         titulo='Editar Candidato')

@app.route('/candidatos/<string:cedula>/desactivar', methods=['POST'])
@login_required
@require_role(['admin', 'reclutador'])
def desactivar_candidato(cedula):
    """Desactiva un candidato (solo cambia estado activo)"""
    candidato = Candidato.get_by_cedula(cedula)
    if candidato:
        candidato.activo = False
        candidato.save()
        flash('🗑️ Candidato desactivado', 'info')
    return redirect(url_for('lista_candidatos'))

@app.route('/candidatos/<string:cedula>/activar', methods=['POST'])
@login_required
@require_role(['admin', 'reclutador'])
def activar_candidato(cedula):
    """Activa un candidato (solo cambia estado activo)"""
    candidato = Candidato.get_by_cedula(cedula)
    if candidato:
        candidato.activo = True
        candidato.save()
        flash('✅ Candidato activado', 'success')
    return redirect(url_for('lista_candidatos'))

@app.route('/candidatos/<string:cedula>/eliminar', methods=['POST'])
@login_required
@require_role(['admin'])  # SOLO ADMIN puede eliminar completamente
def eliminar_candidato(cedula):
    """Elimina completamente un candidato de la base de datos (solo admin)"""
    candidato = Candidato.get_by_cedula(cedula)
    if candidato:
        try:
            # Eliminar referencias, experiencias, postulaciones y luego el candidato
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Eliminar referencias personales
                cursor.execute('DELETE FROM referencias_personales WHERE cedula = %s', (candidato.cedula,))
                
                # Eliminar experiencias
                cursor.execute('DELETE FROM experiencias WHERE cedula = %s', (candidato.cedula,))
                
                # Eliminar postulaciones
                cursor.execute('DELETE FROM postulaciones WHERE candidato_cedula = %s', (candidato.cedula,))
                
                # Eliminar documentos
                cursor.execute('DELETE FROM documentos WHERE cedula = %s', (candidato.cedula,))
                
                # Finalmente eliminar el candidato
                cursor.execute('DELETE FROM candidatos WHERE cedula = %s', (candidato.cedula,))
                
                conn.commit()
            
            flash('🗑️ Candidato eliminado permanentemente de la base de datos', 'success')
        except Exception as e:
            flash(f'❌ Error al eliminar candidato: {str(e)}', 'error')
    return redirect(url_for('lista_candidatos'))

# ============ RUTAS POSTULACIONES ============
@app.route('/postulaciones')
@login_required
@require_role(['admin', 'reclutador', 'gerente'])
def lista_postulaciones():
    estado = request.args.get('estado')
    page = int(request.args.get('page', 1))
    per_page = 10
    
    # Determinar qué postulaciones cargar
    if estado == 'Desactivadas':
        # Cargar postulaciones desactivadas
        postulaciones = Postulacion.get_desactivadas(page=page, per_page=per_page)
        total_postulaciones = Postulacion.get_total_desactivadas()
    else:
        # Cargar postulaciones activas (con o sin filtro de estado)
        postulaciones = Postulacion.get_all(estado=estado, page=page, per_page=per_page)
        total_postulaciones = Postulacion.get_total_count(estado=estado)
    
    # Calcular información de paginación
    total_pages = (total_postulaciones + per_page - 1) // per_page
    has_prev = page > 1
    has_next = page < total_pages
    
    return render_template('postulaciones/lista.html', 
                         postulaciones=postulaciones,
                         estado_filtro=estado,
                         current_page=page,
                         total_pages=total_pages,
                         has_prev=has_prev,
                         has_next=has_next,
                         total_postulaciones=total_postulaciones)

@app.route('/postulaciones/nueva', methods=['GET', 'POST'])
@login_required
@require_role(['admin', 'reclutador', 'gerente'])
def nueva_postulacion():
    form = PostulacionForm()
    if form.validate_on_submit():
        postulacion = Postulacion(
            candidato_cedula=form.candidato_cedula.data,
            cargo_id=form.cargo_id.data,
            estado=form.estado.data,
            fuente_reclutamiento=form.fuente_reclutamiento.data,
            notas=form.notas.data,
            puntaje_evaluacion=form.puntaje_evaluacion.data
        )
        try:
            postulacion.save()
            flash('✅ Postulación registrada exitosamente', 'success')
            return redirect(url_for('lista_postulaciones'))
        except Exception as e:
            flash(f'Error: El candidato ya está postulado a este cargo', 'error')
    
    return render_template('postulaciones/formulario.html', form=form, titulo='Nueva Postulación')

@app.route('/postulaciones/<int:id>')
@login_required
@require_role(['admin', 'reclutador', 'gerente'])
def detalle_postulacion(id):
    postulacion = Postulacion.get_by_id(id)
    if not postulacion:
        flash('Postulación no encontrada', 'error')
        return redirect(url_for('lista_postulaciones'))
    
    siguientes_estados = EstadoPipeline.get_siguientes_estados(postulacion.estado)
    return render_template('postulaciones/detalle.html', 
                         postulacion=postulacion,
                         siguientes_estados=siguientes_estados)

@app.route('/postulaciones/<int:id>/editar', methods=['POST'])
@login_required
@require_role(['admin', 'reclutador', 'gerente'])
def editar_postulacion(id):
    """Edita notas y puntaje de una postulación"""
    postulacion = Postulacion.get_by_id(id)
    if not postulacion:
        flash('Postulación no encontrada', 'error')
        return redirect(url_for('lista_postulaciones'))
    
    # Actualizar notas y puntaje
    notas = request.form.get('notas', '').strip()
    puntaje_evaluacion = request.form.get('puntaje_evaluacion')
    
    postulacion.notas = notas if notas else None
    postulacion.puntaje_evaluacion = float(puntaje_evaluacion) if puntaje_evaluacion and puntaje_evaluacion.strip() else None
    
    try:
        postulacion.save()
        flash('✅ Información de postulación actualizada exitosamente', 'success')
    except Exception as e:
        flash(f'❌ Error al actualizar la postulación: {str(e)}', 'error')
    
    return redirect(url_for('detalle_postulacion', id=id))

@app.route('/postulaciones/<int:id>/cambiar-estado', methods=['POST'])
@login_required
@require_role(['admin', 'reclutador', 'gerente'])
def cambiar_estado_postulacion(id):
    postulacion = Postulacion.get_by_id(id)
    if not postulacion:
        return jsonify({'error': 'No encontrado'}), 404
    
    nuevo_estado = request.form.get('estado')
    if EstadoPipeline.puede_transicionar(postulacion.estado, nuevo_estado):
        postulacion.estado = nuevo_estado
        postulacion.save()
        flash(f'Estado actualizado a: {nuevo_estado}', 'success')
    else:
        flash('Transición de estado no válida', 'error')
    
    return redirect(url_for('detalle_postulacion', id=id))

@app.route('/postulaciones/<int:id>/desactivar', methods=['POST'])
@login_required
@require_role(['admin', 'reclutador', 'gerente'])
def desactivar_postulacion(id):
    """Desactiva una postulación (cambia activo a False)"""
    postulacion = Postulacion.get_by_id(id)
    if postulacion:
        postulacion.activo = False
        postulacion.save()
        flash('🗑️ Postulación desactivada', 'info')
    return redirect(url_for('lista_postulaciones'))

@app.route('/postulaciones/<int:id>/activar', methods=['POST'])
@login_required
@require_role(['admin', 'reclutador', 'gerente'])
def activar_postulacion(id):
    """Activa una postulación (cambia activo a True)"""
    postulacion = Postulacion.get_by_id(id)
    if postulacion:
        postulacion.activo = True
        postulacion.save()
        flash('✅ Postulación activada', 'success')
    return redirect(url_for('lista_postulaciones'))

@app.route('/postulaciones/<int:id>/eliminar', methods=['POST'])
@login_required
@require_role(['admin'])  # SOLO ADMIN puede eliminar completamente
def eliminar_postulacion(id):
    """Elimina completamente una postulación de la base de datos (solo admin)"""
    postulacion = Postulacion.get_by_id(id)
    if postulacion:
        if postulacion.delete():
            flash('🗑️ Postulación eliminada permanentemente de la base de datos', 'success')
        else:
            flash('❌ Error al eliminar la postulación', 'error')
    else:
        flash('❌ Postulación no encontrada', 'error')
    return redirect(url_for('lista_postulaciones'))


# ============ RUTAS DE REPORTES PDF ============
@app.route('/reportes')
@login_required
@require_role(['admin', 'reclutador', 'gerente'])
def reportes():
    """Página principal de reportes"""
    # Obtener cargos activos para el filtro
    cargos = Cargo.get_all(estado='Activo')
    return render_template('reportes/index.html', cargos=cargos)

@app.route('/reportes/candidatos-pdf', methods=['POST'])
@login_required
@require_role(['admin', 'reclutador', 'gerente'])
def reporte_candidatos_pdf():
    """Generar reporte PDF de candidatos"""
    try:
        cargo_id = request.form.get('cargo_id')
        cargo_nombre = "Todas las Vacantes"
        
        if cargo_id and cargo_id != '':
            cargo = Cargo.get_by_id(int(cargo_id))
            if cargo:
                cargo_nombre = f"{cargo.nombre} - {cargo.departamento}"
        
        # Usar la nueva clase ReportGenerator
        from report_generator import ReportGenerator, create_pdf_response
        
        buffer = ReportGenerator.generate_candidatos_por_vacante_report(
            cargo_id=int(cargo_id) if cargo_id else None,
            cargo_nombre=cargo_nombre
        )
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"reporte_candidatos_{timestamp}.pdf"
        
        response = create_pdf_response(buffer, filename)
        return response
        
    except Exception as e:
        flash(f'Error al generar reporte: {str(e)}', 'error')
        return redirect(url_for('reportes'))

@app.route('/reportes/estadisticas-pdf', methods=['POST'])
@login_required
@require_role(['admin', 'reclutador', 'gerente'])
def reporte_estadisticas_pdf():
    """Generar reporte PDF de estadísticas de postulaciones"""
    try:
        fecha_inicio = request.form.get('fecha_inicio')
        fecha_fin = request.form.get('fecha_fin')
        
        # Generar reporte de estadísticas
        buffer = report_generator.generate_estadisticas_postulaciones_report(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )
        
        # Crear nombre de archivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"reporte_estadisticas_{timestamp}.pdf"
        
        response = create_pdf_response(buffer, filename)
        if response is None:
            flash('Error: No se pudo generar el PDF. Verifique que la librería reportlab esté instalada.', 'error')
            return redirect(url_for('reportes'))
        
        return response
        
    except Exception as e:
        flash(f'Error al generar reporte: {str(e)}', 'error')
        return redirect(url_for('reportes'))

# ============ ADMINISTRACIÓN DE USUARIOS ============
@app.route('/admin/usuarios')
@login_required
@require_role(['admin'])
def lista_usuarios():
    """Lista todos los usuarios del sistema (solo administradores)"""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.id_usuario, u.nombre_usuario, u.email, u.rol_id, u.activo, u.created_at,
                   CASE u.rol_id
                       WHEN 1 THEN 'Administrador'
                       WHEN 2 THEN 'Reclutador'
                       WHEN 3 THEN 'Gerente RRHH'
                       WHEN 4 THEN 'Candidato'
                       ELSE 'Desconocido'
                   END as rol_nombre
            FROM usuarios u
            ORDER BY u.created_at DESC
        ''')
        usuarios = cursor.fetchall()
    
    return render_template('admin/usuarios_lista.html', usuarios=usuarios)

@app.route('/admin/usuarios/nuevo', methods=['GET', 'POST'])
@login_required
@require_role(['admin'])
def crear_usuario_admin():
    """Crear un nuevo usuario con cualquier rol (solo administradores)"""
    from forms import RegisterForm
    
    form = RegisterForm()
    
    # Para administración, mostrar todos los roles disponibles
    form.rol.choices = [
        (1, 'Administrador'),
        (2, 'Reclutador'),
        (3, 'Gerente RRHH'),
        (4, 'Candidato')
    ]
    
    if form.validate_on_submit():
        # Validación adicional: verificar que las contraseñas coincidan
        if form.password.data != form.password_confirm.data:
            flash('Las contraseñas no coinciden. Por favor verifica e intenta nuevamente.', 'error')
            return render_template('admin/usuarios_crear.html', form=form)
        
        try:
            # Validación de seguridad: solo admin puede crear otros admins
            if form.rol.data == 1 and current_user.rol_id != 1:
                flash('Solo los administradores pueden crear otros administradores.', 'error')
                return render_template('admin/usuarios_crear.html', form=form)
            
            # Generar nombre_usuario automáticamente desde el email
            nombre_usuario = form.email.data.split('@')[0]
            
            # Si el nombre_usuario ya existe, agregar un sufijo
            contador = 1
            nombre_usuario_original = nombre_usuario
            with db.get_connection() as conn:
                cursor = conn.cursor()
                while True:
                    cursor.execute('SELECT id_usuario FROM usuarios WHERE nombre_usuario = %s', (nombre_usuario,))
                    if not cursor.fetchone():
                        break
                    nombre_usuario = f"{nombre_usuario_original}{contador}"
                    contador += 1
            
            usuario = Usuario(
                nombre_usuario=nombre_usuario,
                email=form.email.data,
                rol_id=form.rol.data,  # Permitir cualquier rol para administración
                activo=True
            )
            usuario.set_password(form.password.data)
            usuario.save()
            
            # Log de auditoría
            import logging
            logging.info(f"ADMIN {current_user.nombre_usuario} creó usuario {usuario.email} con rol {usuario.rol_id}")
            
            flash(f'Usuario "{usuario.email}" creado exitosamente con rol {form.rol.data}', 'success')
            return redirect(url_for('lista_usuarios'))
        except Exception as e:
            flash(f'Error al crear el usuario: {str(e)}', 'error')
    
    return render_template('admin/usuarios_crear.html', form=form)
# ============ HEALTH CHECK PARA RENDER ============
@app.route('/debug/auth')
def debug_auth_endpoint():
    """Endpoint de diagnóstico para autenticación"""
    try:
        from datetime import datetime
        from database import db, get_db_type
        from models import Usuario
        
        debug_info = {
            'timestamp': datetime.now().isoformat(),
            'db_type': get_db_type(),
            'connection_test': False,
            'users_count': 0,
            'roles_count': 0,
            'admin_user': None,
            'error': None
        }
        
        # Probar conexión
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 as test, NOW() as tiempo")
                result = cursor.fetchone()
                debug_info['connection_test'] = True
                debug_info['connection_result'] = str(result)
        except Exception as e:
            debug_info['error'] = f"Connection error: {str(e)}"
            return jsonify(debug_info)
        
        # Contar usuarios
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM usuarios")
                result = cursor.fetchone()
                debug_info['users_count'] = result['count'] if isinstance(result, dict) else result[0]
        except Exception as e:
            debug_info['error'] = f"Users count error: {str(e)}"
        
        # Contar roles
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM roles")
                result = cursor.fetchone()
                debug_info['roles_count'] = result['count'] if isinstance(result, dict) else result[0]
        except Exception as e:
            debug_info['error'] = f"Roles count error: {str(e)}"
        
        # Probar usuario admin
        try:
            admin_user = Usuario.get_by_email_or_username('admin@reclutamiento.com')
            if admin_user:
                debug_info['admin_user'] = {
                    'id': admin_user.id_usuario,
                    'username': admin_user.nombre_usuario,
                    'email': admin_user.email,
                    'active': admin_user.activo,
                    'role': admin_user.rol_nombre,
                    'password_hash_length': len(admin_user.password_hash) if admin_user.password_hash else 0
                }
                
                # Probar contraseña
                debug_info['admin_user']['password_check'] = admin_user.check_password('Admin123!')
            else:
                debug_info['admin_user'] = 'NOT_FOUND'
        except Exception as e:
            debug_info['error'] = f"Admin user error: {str(e)}"
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({
            'error': f"General error: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/health')
def health_check():
    """Endpoint para verificar que la app está viva (usado por Render)"""
    try:
        # Health check ultra simple sin dependencias
        import time
        return jsonify({
            'status': 'healthy',
            'timestamp': int(time.time()),
            'service': 'reclutamiento-web',
            'version': '1.0.0',
            'environment': os.environ.get('FLASK_ENV', 'unknown')
        }), 200
    except Exception as e:
        # Si algo falla, responder con error pero con código 200 para no detener el deploy
        import time
        return jsonify({
            'status': 'unhealthy',
            'timestamp': int(time.time()),
            'service': 'reclutamiento-web',
            'error': str(e),
            'environment': os.environ.get('FLASK_ENV', 'unknown')
        }), 200

if __name__ == '__main__':
    # Configuración para desarrollo local
    app.run(debug=True, port=5000)
else:
    # Configuración para producción (Render.com)
    # Render establece las variables de entorno automáticamente
    # La aplicación será servida por Gunicorn, no por Flask directamente
    pass
