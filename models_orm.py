"""
Modelos de datos compatibles con SQLAlchemy ORM
Reemplaza las consultas SQL raw por operaciones ORM para compatibilidad MySQL/SQLite
"""

from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey, DECIMAL, DATE, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from config import get_database_uri, get_mysql_config
import pymysql
import sqlite3
from contextlib import contextmanager

Base = declarative_base()

class Rol(Base):
    __tablename__ = 'roles'
    
    id_rol = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(50), unique=True, nullable=False)
    descripcion = Column(Text)
    
    # Relaciones
    usuarios = relationship("Usuario", back_populates="rol")

class Usuario(Base):
    __tablename__ = 'usuarios'
    
    id_usuario = Column(Integer, primary_key=True, autoincrement=True)
    nombre_usuario = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    rol_id = Column(Integer, ForeignKey('roles.id_rol'), nullable=False)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    ultimo_acceso = Column(DateTime)
    
    # Relaciones
    rol = relationship("Rol", back_populates="usuarios")

class Candidato(Base):
    __tablename__ = 'candidatos'
    
    cedula = Column(String(10), primary_key=True)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    resumen = Column(Text)
    habilidades = Column(Text)
    experiencia_anos = Column(Integer, default=0)
    nivel_educativo = Column(String(100))
    direccion_domicilio = Column(String(100))
    disponibilidad = Column(String(50))
    salario_esperado = Column(DECIMAL(10, 2))
    fecha_registro = Column(DateTime, default=datetime.utcnow)
    activo = Column(Boolean, default=True)

class Cargo(Base):
    __tablename__ = 'cargos'
    
    id_cargo = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    departamento = Column(String(100))
    salario_minimo = Column(DECIMAL(10, 2))
    salario_maximo = Column(DECIMAL(10, 2))
    tipo_contrato = Column(String(50))
    direccion_domicilio = Column(String(100))
    estado = Column(String(50), default='Activo')
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_cierre = Column(DATE)

class Postulacion(Base):
    __tablename__ = 'postulaciones'
    
    id_postulacion = Column(Integer, primary_key=True, autoincrement=True)
    cedula = Column(String(10), ForeignKey('candidatos.cedula'), nullable=False)
    id_cargo = Column(Integer, ForeignKey('cargos.id_cargo'), nullable=False)
    fecha_postulacion = Column(DateTime, default=datetime.utcnow)
    estado = Column(String(50), default='Recibido')
    fuente_reclutamiento = Column(String(100))
    notas = Column(Text)
    puntaje_evaluacion = Column(Integer)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    candidato = relationship("Candidato")
    cargo = relationship("Cargo")

class ReferenciaPersonal(Base):
    __tablename__ = 'referencias_personales'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    cedula = Column(String(10), ForeignKey('candidatos.cedula'), nullable=False)
    nombre = Column(String(100), nullable=False)
    telefono = Column(String(20))
    relacion = Column(String(50))
    descripcion = Column(Text)
    
    # Relaciones
    candidato_ref = relationship("Candidato")

class Experiencia(Base):
    __tablename__ = 'experiencias'
    
    id_experiencia = Column(Integer, primary_key=True, autoincrement=True)
    cedula = Column(String(10), ForeignKey('candidatos.cedula'), nullable=False)
    empresa = Column(String(100), nullable=False)
    cargo = Column(String(100), nullable=False)
    fecha_inicio = Column(DATE, nullable=False)
    fecha_fin = Column(DATE)
    actual = Column(Boolean, default=False)
    descripcion = Column(Text)
    
    # Relaciones
    candidato_exp = relationship("Candidato")

class DatabaseManager:
    """Gestor de base de datos compatible con MySQL y SQLite usando SQLAlchemy ORM"""
    
    def __init__(self):
        self.engine = create_engine(
            get_database_uri(),
            **self._get_engine_options()
        )
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def _get_engine_options(self):
        """Obtener opciones específicas del motor según la base de datos"""
        mysql_config = get_mysql_config()
        if mysql_config:
            return {
                'pool_pre_ping': True,
                'pool_recycle': 300,
                'connect_args': {
                    'charset': 'utf8mb4',
                    **({'ssl': mysql_config.get('ssl')} if mysql_config.get('ssl') else {})
                }
            }
        else:
            return {}
    
    @contextmanager
    def get_session(self):
        """Context manager para sesiones de SQLAlchemy"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def init_database(self):
        """Crear todas las tablas usando SQLAlchemy"""
        Base.metadata.create_all(bind=self.engine)
        
        # Insertar roles por defecto si no existen
        with self.get_session() as session:
            roles_default = [
                ('admin', 'Administrador del sistema'),
                ('reclutador', 'Reclutador'),
                ('gerente', 'Gerente de RRHH'),
                ('candidato', 'Candidato')
            ]
            
            for nombre, descripcion in roles_default:
                # Usar get_or_create para evitar duplicados
                rol = session.query(Rol).filter_by(nombre=nombre).first()
                if not rol:
                    rol = Rol(nombre=nombre, descripcion=descripcion)
                    session.add(rol)
    
    def get_connection(self):
        """Método de compatibilidad con código existente"""
        return self.get_session()

# Instancia global
db = DatabaseManager()
