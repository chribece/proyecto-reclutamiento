from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, FloatField, IntegerField, DateField, EmailField, FieldList, FormField, BooleanField, PasswordField
from wtforms.validators import DataRequired, Email, Optional, NumberRange, Length, Regexp, EqualTo, ValidationError
from datetime import date


class LoginForm(FlaskForm):
    """Formulario para login de usuarios"""
    email = StringField('Email o Nombre de Usuario', validators=[
        DataRequired(message='Email o nombre de usuario es obligatorio')
    ])
    password = PasswordField('Contraseña', validators=[
        DataRequired(message='La contraseña es obligatoria'),
        Length(min=6, message='La contraseña debe tener al menos 6 caracteres')
    ])
    
    def validate_email(self, field):
        from models import Usuario
        # Buscar por email O nombre_usuario
        usuario = Usuario.get_by_email_or_username(field.data)
        if not usuario:
            raise ValidationError('Usuario/email o contraseña incorrectos')


class RegisterForm(FlaskForm):
    """Formulario para registro de nuevos usuarios"""
    email = EmailField('Correo Electrónico', validators=[
        DataRequired(message='El email es obligatorio'),
        Email(message='Email inválido')
    ])
    password = PasswordField('Contraseña', validators=[
        DataRequired(message='La contraseña es obligatoria'),
        Length(min=6, message='La contraseña debe tener al menos 6 caracteres')
    ])
    password_confirm = PasswordField('Confirmar Contraseña', validators=[
        DataRequired(message='Debe confirmar la contraseña'),
        EqualTo('password', message='Las contraseñas no coinciden')
    ])
    rol = SelectField('Rol', coerce=int, choices=[
        (4, 'Candidato')  # Solo Candidato disponible para registro público
    ], default=4, validators=[DataRequired()])
    
    def validate_email(self, field):
        from models import Usuario
        if Usuario.get_by_email(field.data):
            raise ValidationError('El email ya está registrado')


class CargoForm(FlaskForm):
    nombre = StringField('Nombre de la Vacante', validators=[
        DataRequired(message='El nombre es obligatorio'),
        Length(min=3, max=100)
    ])
    descripcion = TextAreaField('Descripción', validators=[Length(max=2000)])
    departamento = StringField('Departamento', validators=[DataRequired(), Length(min=2, max=50)])
    salario_minimo = FloatField('Salario Mínimo', validators=[Optional(), NumberRange(min=0)])
    salario_maximo = FloatField('Salario Máximo', validators=[Optional(), NumberRange(min=0)])
    tipo_contrato = SelectField('Tipo de Contrato', choices=[
        ('Tiempo completo', 'Tiempo completo'),
        ('Medio tiempo', 'Medio tiempo'),
        ('Freelance', 'Freelance'),
        ('Prácticas', 'Prácticas')
    ], validators=[DataRequired()])
    id_sucursal = SelectField('Sucursal', coerce=int, validators=[DataRequired(message='Debe seleccionar una sucursal')])
    estado = SelectField('Estado', choices=[
        ('Activo', 'Activo'),
        ('Pausado', 'Pausado'),
        ('Cerrado', 'Cerrado')
    ], default='Activo')
    fecha_cierre = DateField('Fecha de Cierre', validators=[Optional()], format='%Y-%m-%d')
    
    def __init__(self, *args, **kwargs):
        super(CargoForm, self).__init__(*args, **kwargs)
        # Cargar sucursales disponibles
        from database import db
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id_sucursal, nombre FROM sucursales WHERE activa = 1 ORDER BY nombre')
            self.id_sucursal.choices = [(row['id_sucursal'], row['nombre']) for row in cursor.fetchall()]


class ReferenciaForm(FlaskForm):
    nombre = StringField('Nombre completo', validators=[DataRequired(), Length(max=100)])
    telefono = StringField('Teléfono', validators=[DataRequired(), Length(max=20)])
    relacion = StringField('Relación', validators=[Optional(), Length(max=50)])
    descripcion = StringField('Descripción', default='No aplica', validators=[Length(max=200)])


class ExperienciaForm(FlaskForm):
    empresa = StringField('Empresa', validators=[DataRequired(), Length(max=100)])
    cargo = StringField('Cargo', validators=[DataRequired(), Length(max=100)])
    fecha_inicio = DateField('Fecha inicio', validators=[DataRequired()], format='%Y-%m-%d')
    fecha_fin = DateField('Fecha fin', validators=[Optional()], format='%Y-%m-%d')
    actual = BooleanField('Trabajo actual')
    descripcion = TextAreaField('Descripción', validators=[Optional(), Length(max=500)])


class CandidatoForm(FlaskForm):
    # Datos personales
    cedula = StringField('Cédula (10 dígitos)', validators=[
        DataRequired(),
        Regexp(r'^\d{10}$', message='La cédula debe tener exactamente 10 dígitos numéricos')
    ])
    nombre = StringField('Nombre', validators=[DataRequired(), Length(min=2, max=50)])
    apellido = StringField('Apellido', validators=[DataRequired(), Length(min=2, max=50)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    telefono = StringField('Teléfono', validators=[Optional(), Length(max=20)])
    
    # Vacante a aplicar (solo para administradores)
    cargo_id = SelectField('Vacante a la que aplica', coerce=int, validators=[Optional()])
    
    # Información profesional
    resumen = TextAreaField('Resumen Profesional', validators=[Optional(), Length(max=3000)])
    habilidades = StringField('Habilidades (separadas por coma)', validators=[Optional(), Length(max=500)])
    experiencia_anos = IntegerField('Años de Experiencia Total', validators=[Optional(), NumberRange(min=0, max=50)])
    nivel_educativo = SelectField('Nivel Educativo', choices=[
        ('', 'Seleccione...'),
        ('Técnico', 'Técnico'),
        ('Universitario', 'Universitario'),
        ('Posgrado', 'Posgrado'),
        ('Doctorado', 'Doctorado')
    ], validators=[Optional()])
    direccion_domicilio = StringField('Dirección de Domicilio', validators=[Optional(), Length(max=100)])
    disponibilidad = SelectField('Disponibilidad', choices=[
        ('Inmediata', 'Inmediata'),
        ('2 semanas', '2 semanas'),
        ('1 mes', '1 mes'),
        ('Más de 1 mes', 'Más de 1 mes')
    ], default='2 semanas')
    salario_esperado = FloatField('Salario Esperado', validators=[Optional(), NumberRange(min=0)])
    
    def __init__(self, *args, **kwargs):
        super(CandidatoForm, self).__init__(*args, **kwargs)
        # Cargar vacantes disponibles solo si se necesita
        if hasattr(self, 'cargo_id') and self.cargo_id.validators:
            from models import Cargo
            self.cargo_id.choices = [(c.id_cargo, f"{c.nombre} - {c.departamento}") 
                                    for c in Cargo.get_all(estado='Activo')]


class CandidatoRegistroForm(FlaskForm):
    """Formulario específico para registro de candidatos (sin cargo_id)"""
    # Datos personales
    cedula = StringField('Cédula (10 dígitos)', validators=[
        DataRequired(),
        Regexp(r'^\d{10}$', message='La cédula debe tener exactamente 10 dígitos numéricos')
    ])
    nombre = StringField('Nombre', validators=[DataRequired(), Length(min=2, max=50)])
    apellido = StringField('Apellido', validators=[DataRequired(), Length(min=2, max=50)])
    email = EmailField('Email', validators=[Optional()])  # Hacer opcional para candidatos
    telefono = StringField('Teléfono', validators=[Optional(), Length(max=20)])
    
    # Información profesional
    resumen = TextAreaField('Resumen Profesional', validators=[Optional(), Length(max=3000)])
    habilidades = StringField('Habilidades (separadas por coma)', validators=[Optional(), Length(max=500)])
    experiencia_anos = IntegerField('Años de Experiencia Total', validators=[Optional(), NumberRange(min=0, max=50)])
    nivel_educativo = SelectField('Nivel Educativo', choices=[
        ('', 'Seleccione...'),
        ('Técnico', 'Técnico'),
        ('Universitario', 'Universitario'),
        ('Posgrado', 'Posgrado'),
        ('Doctorado', 'Doctorado')
    ], validators=[Optional()])
    direccion_domicilio = StringField('Dirección de Domicilio', validators=[Optional(), Length(max=100)])
    disponibilidad = SelectField('Disponibilidad', choices=[
        ('Inmediata', 'Inmediata'),
        ('2 semanas', '2 semanas'),
        ('1 mes', '1 mes'),
        ('Más de 1 mes', 'Más de 1 mes')
    ], default='2 semanas')
    salario_esperado = FloatField('Salario Esperado', validators=[Optional(), NumberRange(min=0)])


class PostulacionForm(FlaskForm):
    candidato_cedula = StringField('Cédula Candidato', validators=[DataRequired(), Length(min=10, max=10)])
    cargo_id = SelectField('Cargo', coerce=int, validators=[DataRequired()])
    estado = SelectField('Estado', coerce=str, validators=[DataRequired()])
    fuente_reclutamiento = SelectField('Fuente de Reclutamiento', choices=[
        ('', 'Seleccione una fuente...'),
        ('LinkedIn', 'LinkedIn'),
        ('Referido', 'Referido interno'),
        ('Web corporativa', 'Web corporativa'),
        ('Bolsa de empleo', 'Bolsa de empleo'),
        ('Otro', 'Otro')
    ], validators=[Optional()])
    notas = TextAreaField('Notas', validators=[Optional(), Length(max=2000)])
    puntaje_evaluacion = IntegerField('Puntaje (1-10)', validators=[Optional(), NumberRange(min=1, max=10)])
    
    def __init__(self, *args, **kwargs):
        super(PostulacionForm, self).__init__(*args, **kwargs)
        from models import Cargo
        
        # Cargar cargos activos
        self.cargo_id.choices = [(c.id_cargo, f"{c.nombre} ({c.departamento})") 
                                for c in Cargo.get_all(estado='Activo')]
        
        # Usar estados corregidos de la base de datos (sin tildes)
        estados_correctos = [
            ('Recibido', 'Recibido'),
            ('En revision', 'En revision'),
            ('Entrevista tecnica', 'Entrevista tecnica'),
            ('Entrevista RRHH', 'Entrevista RRHH'),
            ('Oferta', 'Oferta'),
            ('Contratado', 'Contratado'),
            ('Rechazado', 'Rechazado'),
            ('Descartado', 'Descartado')
        ]
        self.estado.choices = estados_correctos
        self.estado.default = 'Recibido'


class BusquedaCandidatoForm(FlaskForm):
    query = StringField('Buscar', validators=[Optional()])
    habilidad = StringField('Habilidad', validators=[Optional()])
    experiencia_min = IntegerField('Exp. Mínima', validators=[Optional(), NumberRange(min=0)])
    disponibilidad = SelectField('Disponibilidad', choices=[
        ('', 'Todas'),
        ('Inmediata', 'Inmediata'),
        ('2 semanas', '2 semanas'),
        ('1 mes', '1 mes'),
        ('Más de 1 mes', 'Más de 1 mes')
    ], validators=[Optional()])