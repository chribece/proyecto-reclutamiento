import pymysql
import sqlite3
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import json
from database import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

def get_active_value():
    """Obtiene el valor correcto para 'activo' según el tipo de BD"""
    return 'TRUE' if db.db_type == 'postgresql' else '1'

@dataclass
class Usuario(UserMixin):
    """Modelo para autenticación de usuarios"""
    id_usuario: Optional[int] = None
    nombre_usuario: str = ""
    email: str = ""
    password_hash: str = ""
    rol_id: int = 4  # 4 = candidato por defecto
    activo: bool = True
    created_at: Optional[datetime] = None
    ultimo_acceso: Optional[datetime] = None
    rol_nombre: str = "candidato"
    
    def get_id(self):
        """Requerido por Flask-Login"""
        return str(self.id_usuario)
    
    @classmethod
    def from_row(cls, row) -> 'Usuario':
        """Conversión ultra-simple y robusta"""
        try:
            # Manejar tanto diccionarios como tuplas
            if isinstance(row, dict):
                return cls(
                    id_usuario=row.get('id_usuario'),
                    nombre_usuario=row.get('nombre_usuario', ''),
                    email=row.get('email', ''),
                    password_hash=row.get('password_hash', ''),
                    rol_id=row.get('rol_id', 4),
                    activo=bool(row.get('activo')) if row.get('activo') is not None else True,
                    created_at=row.get('created_at'),
                    ultimo_acceso=row.get('ultimo_acceso'),
                    rol_nombre=row.get('rol_nombre', 'candidato')
                )
            elif isinstance(row, (tuple, list)):
                return cls(
                    id_usuario=row[0] if len(row) > 0 else None,
                    nombre_usuario=row[1] if len(row) > 1 else '',
                    email=row[2] if len(row) > 2 else '',
                    password_hash=row[3] if len(row) > 3 else '',
                    rol_id=row[4] if len(row) > 4 else 4,
                    activo=bool(row[5]) if len(row) > 5 and row[5] is not None else True,
                    created_at=row[6] if len(row) > 6 else None,
                    ultimo_acceso=row[7] if len(row) > 7 else None,
                    rol_nombre=row[8] if len(row) > 8 else 'candidato'
                )
            else:
                # Valores por defecto si no se puede procesar
                return cls(
                    id_usuario=None,
                    nombre_usuario='',
                    email='',
                    password_hash='',
                    rol_id=4,
                    activo=True,
                    created_at=None,
                    ultimo_acceso=None,
                    rol_nombre='candidato'
                )
        except Exception as e:
            print(f"Error en from_row: {e}")
            # Retornar usuario vacío en caso de error
            return cls(
                id_usuario=None,
                nombre_usuario='',
                email='',
                password_hash='',
                rol_id=4,
                activo=True,
                created_at=None,
                ultimo_acceso=None,
                rol_nombre='candidato'
            )
    
    def set_password(self, password: str):
        """Hash y guarda la contraseña"""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password: str) -> bool:
        """Verifica la contraseña"""
        return check_password_hash(self.password_hash, password)
    
    def save(self) -> int:
        """Guarda o actualiza el usuario con manejo de duplicados compatible MySQL/SQLite"""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                if self.id_usuario:
                    # Usar valores correctos según tipo de BD
                    if db.db_type == 'postgresql':
                        activo_value = 'TRUE' if self.activo else 'FALSE'
                    else:
                        activo_value = 1 if self.activo else 0
                    
                    cursor.execute(f'''
                        UPDATE usuarios 
                        SET nombre_usuario=%s, email=%s, password_hash=%s, 
                            rol_id=%s, activo={activo_value}, ultimo_acceso=NOW()
                            WHERE id_usuario=%s
                    ''', (self.nombre_usuario, self.email, self.password_hash,
                          self.rol_id, self.id_usuario))
                    return self.id_usuario
                else:
                    # Usar valores correctos según tipo de BD
                    if db.db_type == 'postgresql':
                        activo_value = 'TRUE' if self.activo else 'FALSE'
                    else:
                        activo_value = 1 if self.activo else 0
                    
                    cursor.execute(f'''
                        INSERT INTO usuarios (nombre_usuario, email, password_hash, rol_id, activo)
                        VALUES (%s, %s, %s, %s, {activo_value})
                    ''', (self.nombre_usuario, self.email, self.password_hash,
                          self.rol_id))
                    return cursor.lastrowid
            except (pymysql.err.IntegrityError, sqlite3.IntegrityError) as e:
                # Manejar duplicados de forma compatible con ambos motores
                conn.rollback()
                if 'Duplicate entry' in str(e) or 'UNIQUE constraint failed' in str(e):
                    # Si es un duplicado, buscar el usuario existente
                    if self.email:
                        existing = self.get_by_email(self.email)
                    else:
                        existing = self.get_by_username(self.nombre_usuario)
                    if existing:
                        return existing.id_usuario
                raise e
    
    @classmethod
    def get_by_username(cls, nombre_usuario: str) -> Optional['Usuario']:
        """Obtiene usuario por nombre de usuario"""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                SELECT u.*, r.nombre as rol_nombre 
                FROM usuarios u
                LEFT JOIN roles r ON u.rol_id = r.id_rol
                WHERE u.nombre_usuario = %s AND u.activo = {get_active_value()}
                LIMIT 1
            ''', (nombre_usuario,))
            row = cursor.fetchone()
            return cls.from_row(row) if row else None
    
    @classmethod
    def get_by_email(cls, email: str) -> Optional['Usuario']:
        """Obtiene usuario por email"""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                SELECT u.*, r.nombre as rol_nombre 
                FROM usuarios u
                LEFT JOIN roles r ON u.rol_id = r.id_rol
                WHERE u.email = %s AND u.activo = {get_active_value()}
                LIMIT 1
            ''', (email,))
            row = cursor.fetchone()
            return cls.from_row(row) if row else None
    
    @classmethod
    def get_by_email_or_username(cls, credential: str) -> Optional['Usuario']:
        """Obtiene usuario por email O nombre_usuario - para flexibilidad en login"""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Usar valor según tipo de base de datos
            if db.db_type == 'postgresql':
                active_value = 'TRUE'
            else:
                active_value = '1'
            
            cursor.execute(f'''
                SELECT u.*, r.nombre as rol_nombre 
                FROM usuarios u
                LEFT JOIN roles r ON u.rol_id = r.id_rol
                WHERE (u.email = %s OR u.nombre_usuario = %s) AND u.activo = {active_value}
                LIMIT 1
            ''', (credential, credential))
            row = cursor.fetchone()
            return cls.from_row(row) if row else None
    
    @classmethod
    def get_by_id(cls, id_usuario: int) -> Optional['Usuario']:
        """Obtiene usuario por ID"""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                SELECT u.*, r.nombre as rol_nombre 
                FROM usuarios u
                LEFT JOIN roles r ON u.rol_id = r.id_rol
                WHERE u.id_usuario = %s AND u.activo = {get_active_value()}
                LIMIT 1
            ''', (id_usuario,))
            row = cursor.fetchone()
            return cls.from_row(row) if row else None
    
    def has_role(self, role_name: str) -> bool:
        """Verifica si el usuario tiene un rol específico"""
        return self.rol_nombre == role_name
    
    def is_admin(self) -> bool:
        return self.rol_nombre == 'admin'
    
    def is_reclutador(self) -> bool:
        return self.rol_nombre in ['admin', 'reclutador']
    
    def is_gerente(self) -> bool:
        return self.rol_nombre in ['admin', 'gerente']


@dataclass
class Cargo:
    id_cargo: Optional[int] = None
    nombre: str = ""
    descripcion: str = ""
    departamento: str = ""
    salario_minimo: float = 0.0
    salario_maximo: float = 0.0
    tipo_contrato: str = "Tiempo completo"
    direccion_domicilio: str = ""
    id_sucursal: Optional[int] = None
    nombre_sucursal: str = ""
    estado: str = "Activo"
    fecha_creacion: Optional[datetime] = None
    fecha_cierre: Optional[date] = None
    
    @classmethod
    def from_row(cls, row: Dict) -> 'Cargo':
        fecha_cierre = row.get('fecha_cierre')
        if fecha_cierre and isinstance(fecha_cierre, str):
            try:
                fecha_cierre = datetime.strptime(fecha_cierre, '%Y-%m-%d').date()
            except ValueError:
                fecha_cierre = None
        
        return cls(
            id_cargo=row.get('id_cargo'),
            nombre=row.get('nombre', ''),
            descripcion=row.get('descripcion', ''),
            departamento=row.get('departamento', ''),
            salario_minimo=row.get('salario_minimo') or 0.0,
            salario_maximo=row.get('salario_maximo') or 0.0,
            tipo_contrato=row.get('tipo_contrato', 'Tiempo completo'),
            direccion_domicilio=row.get('direccion_domicilio', ''),
            id_sucursal=row.get('id_sucursal'),
            nombre_sucursal=row.get('nombre_sucursal', ''),
            estado=row.get('estado', 'Activo'),
            fecha_creacion=row.get('fecha_creacion'),
            fecha_cierre=fecha_cierre
        )
    
    def save(self) -> int:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            if self.id_cargo:
                cursor.execute('''
                    UPDATE cargos SET nombre=%s, descripcion=%s, departamento=%s, 
                    salario_minimo=%s, salario_maximo=%s, tipo_contrato=%s, 
                    id_sucursal=%s, estado=%s, fecha_cierre=%s WHERE id_cargo=%s
                ''', (self.nombre, self.descripcion, self.departamento,
                      self.salario_minimo, self.salario_maximo, self.tipo_contrato,
                      self.id_sucursal, self.estado, self.fecha_cierre, self.id_cargo))
                return self.id_cargo
            else:
                cursor.execute('''
                    INSERT INTO cargos (nombre, descripcion, departamento, salario_minimo, 
                    salario_maximo, tipo_contrato, id_sucursal, estado, fecha_cierre)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (self.nombre, self.descripcion, self.departamento, self.salario_minimo,
                      self.salario_maximo, self.tipo_contrato, self.id_sucursal, self.estado, self.fecha_cierre))
                return cursor.lastrowid
    
    @classmethod
    def get_by_id(cls, id_cargo: int) -> Optional['Cargo']:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT c.*, s.nombre as nombre_sucursal 
                FROM cargos c 
                LEFT JOIN sucursales s ON c.id_sucursal = s.id_sucursal 
                WHERE c.id_cargo = %s
            ''', (id_cargo,))
            row = cursor.fetchone()
            return cls.from_row(row) if row else None
    
    @classmethod
    def get_all(cls, estado: Optional[str] = None) -> List['Cargo']:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            if estado:
                cursor.execute('''
                    SELECT c.*, s.nombre as nombre_sucursal 
                    FROM cargos c 
                    LEFT JOIN sucursales s ON c.id_sucursal = s.id_sucursal 
                    WHERE c.estado = %s 
                    ORDER BY c.fecha_creacion DESC
                ''', (estado,))
            else:
                cursor.execute('''
                    SELECT c.*, s.nombre as nombre_sucursal 
                    FROM cargos c 
                    LEFT JOIN sucursales s ON c.id_sucursal = s.id_sucursal 
                    ORDER BY c.fecha_creacion DESC
                ''')
            return [cls.from_row(row) for row in cursor.fetchall()]
    
    def delete(self) -> bool:
        if not self.id_cargo:
            return False
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM cargos WHERE id_cargo = %s', (self.id_cargo,))
            return cursor.rowcount > 0
    
    def get_postulaciones_count(self) -> int:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) as count FROM postulaciones WHERE id_cargo = %s', (self.id_cargo,))
            result = cursor.fetchone()
            return result['count'] if result else 0
    
    @property
    def id(self) -> Optional[int]:
        """Alias for id_cargo for compatibility with templates"""
        return self.id_cargo


@dataclass
class Candidato:
    cedula: str = ""
    nombre: str = ""
    apellido: str = ""
    email: str = ""
    telefono: str = ""
    resumen: str = ""
    habilidades: List[str] = field(default_factory=list)
    experiencia_anos: int = 0
    nivel_educativo: str = ""
    direccion_domicilio: str = ""
    disponibilidad: str = "2 semanas"
    salario_esperado: float = 0.0
    fecha_registro: Optional[datetime] = None
    activo: bool = True
    
    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido}"
    
    @classmethod
    def from_row(cls, row: Dict) -> 'Candidato':
        habilidades = []
        if row.get('habilidades'):
            try:
                habilidades = json.loads(row['habilidades'])
            except:
                habilidades = row['habilidades'].split(',') if isinstance(row['habilidades'], str) else []
        
        return cls(
            cedula=row.get('cedula', ''),
            nombre=row.get('nombre', ''),
            apellido=row.get('apellido', ''),
            email=row.get('email', ''),
            telefono=row.get('telefono', ''),
            resumen=row.get('resumen', ''),
            habilidades=habilidades,
            experiencia_anos=row.get('experiencia_anos') or 0,
            nivel_educativo=row.get('nivel_educativo', ''),
            direccion_domicilio=row.get('direccion_domicilio', ''),
            disponibilidad=row.get('disponibilidad', '2 semanas'),
            salario_esperado=row.get('salario_esperado') or 0.0,
            fecha_registro=row.get('fecha_registro'),
            activo=bool(row.get('activo', True))
        )
    
    def save(self) -> str:
        habilidades_json = json.dumps(self.habilidades) if self.habilidades else '[]'
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                # Usar valores correctos según tipo de BD
                if db.db_type == 'postgresql':
                    activo_value = 'TRUE' if self.activo else 'FALSE'
                else:
                    activo_value = 1 if self.activo else 0
                
                # Verificar si el candidato ya existe
                cursor.execute('SELECT cedula FROM candidatos WHERE cedula = %s', (self.cedula,))
                existing = cursor.fetchone()
                
                if existing:
                    # Actualizar candidato existente
                    cursor.execute(f'''
                        UPDATE candidatos SET nombre=%s, apellido=%s, email=%s, telefono=%s, resumen=%s, 
                        habilidades=%s, experiencia_anos=%s, nivel_educativo=%s, direccion_domicilio=%s,
                        disponibilidad=%s, salario_esperado=%s, activo={activo_value}
                        WHERE cedula=%s
                    ''', (self.nombre, self.apellido, self.email, self.telefono, self.resumen,
                          habilidades_json, self.experiencia_anos, self.nivel_educativo,
                          self.direccion_domicilio, self.disponibilidad, self.salario_esperado, 
                          self.cedula))
                else:
                    # Insertar nuevo candidato
                    cursor.execute(f'''
                        INSERT INTO candidatos (cedula, nombre, apellido, email, telefono, resumen,
                        habilidades, experiencia_anos, nivel_educativo, direccion_domicilio, 
                        disponibilidad, salario_esperado, activo)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, {activo_value})
                    ''', (self.cedula, self.nombre, self.apellido, self.email, self.telefono, self.resumen,
                          habilidades_json, self.experiencia_anos, self.nivel_educativo,
                          self.direccion_domicilio, self.disponibilidad, self.salario_esperado))
                
                conn.commit()
                return self.cedula
            except pymysql.err.IntegrityError:
                # Email duplicado
                raise Exception("El email ya está registrado")
    
    @classmethod
    def get_by_cedula(cls, cedula: str) -> Optional['Candidato']:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM candidatos WHERE cedula = %s', (cedula,))
            row = cursor.fetchone()
            return cls.from_row(row) if row else None
    
    @classmethod
    def get_all(cls, activo: Optional[bool] = None) -> List['Candidato']:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            if activo is not None:
                # Usar valor boolean correcto según tipo de BD
                from database import get_db_type
                if get_db_type() == 'postgresql':
                    cursor.execute(f'SELECT * FROM candidatos WHERE activo = {str(activo).upper()} ORDER BY fecha_registro DESC')
                else:
                    cursor.execute('SELECT * FROM candidatos WHERE activo = %s ORDER BY fecha_registro DESC', (int(activo),))
            else:
                cursor.execute('SELECT * FROM candidatos ORDER BY fecha_registro DESC')
            return [cls.from_row(row) for row in cursor.fetchall()]
    
    @classmethod
    def get_paginated(cls, page: int = 1, per_page: int = 5, activo: Optional[bool] = None, 
                      busqueda: str = '', disponibilidad: str = '') -> Dict[str, Any]:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            offset = (page - 1) * per_page
            
            # Construir consulta dinámica con filtros
            conditions = []
            params = []
            
            # 1. Filtro activo
            if activo is not None:
                # Usar valor boolean correcto según tipo de BD
                from database import get_db_type
                if get_db_type() == 'postgresql':
                    conditions.append(f'activo = {str(activo).upper()}')
                else:
                    conditions.append('activo = %s')
                    params.append(int(activo))
            
            # 2. Filtro búsqueda (nombre, email, teléfono, habilidades)
            if busqueda:
                conditions.append('(nombre LIKE %s OR apellido LIKE %s OR email LIKE %s OR telefono LIKE %s OR habilidades LIKE %s)')
                search_term = f'%{busqueda}%'
                params.extend([search_term, search_term, search_term, search_term, search_term])
            
            # 3. Filtro disponibilidad
            if disponibilidad:
                conditions.append('disponibilidad = %s')
                params.append(disponibilidad)
            
            # Construir WHERE clause
            where_clause = ''
            if conditions:
                where_clause = 'WHERE ' + ' AND '.join(conditions)
            
            # Obtener total de registros
            cursor.execute(f'SELECT COUNT(*) as total FROM candidatos {where_clause}', params)
            total = cursor.fetchone()['total']
            
            # Obtener registros para la página actual
            query = f'SELECT * FROM candidatos {where_clause} ORDER BY fecha_registro DESC LIMIT %s OFFSET %s'
            params.extend([per_page, offset])
            cursor.execute(query, params)
            
            candidatos = [cls.from_row(row) for row in cursor.fetchall()]
            
            # Calcular información de paginación
            total_pages = (total + per_page - 1) // per_page if total > 0 else 1
            has_prev = page > 1
            has_next = page < total_pages
            
            return {
                'candidatos': candidatos,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': total_pages,
                'has_prev': has_prev,
                'has_next': has_next,
                'prev_num': page - 1 if has_prev else None,
                'next_num': page + 1 if has_next else None
            }


    
    def delete(self) -> bool:
        if not self.cedula:
            return False
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM candidatos WHERE cedula = %s', (self.cedula,))
            return cursor.rowcount > 0


@dataclass
class Postulacion:
    id_postulacion: Optional[int] = None
    cedula: str = ""
    id_cargo: int = 0
    fecha_postulacion: Optional[datetime] = None
    estado: str = "Recibido"
    fuente_reclutamiento: str = ""
    notas: str = ""
    puntaje_evaluacion: Optional[int] = None
    fecha_actualizacion: Optional[datetime] = None
    activo: bool = True
    
    candidato: Optional[Candidato] = None
    cargo: Optional[Cargo] = None
    
    @classmethod
    def from_row(cls, row: Dict) -> 'Postulacion':
        return cls(
            id_postulacion=row.get('id_postulacion'),
            cedula=row.get('cedula', ''),
            id_cargo=row.get('id_cargo', 0),
            fecha_postulacion=row.get('fecha_postulacion'),
            estado=row.get('estado', 'Recibido'),
            fuente_reclutamiento=row.get('fuente_reclutamiento', ''),
            notas=row.get('notas', ''),
            puntaje_evaluacion=row.get('puntaje_evaluacion'),
            fecha_actualizacion=row.get('fecha_actualizacion'),
            activo=bool(row.get('activo', True))
        )
    
    def save(self) -> int:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            if self.id_postulacion:
                # Usar valor boolean correcto según tipo de BD
                if db.db_type == 'postgresql':
                    activo_value = 'TRUE' if self.activo else 'FALSE'
                else:
                    activo_value = 1 if self.activo else 0
                cursor.execute(f'''
                    UPDATE postulaciones SET estado=%s, fuente_reclutamiento=%s, 
                    notas=%s, puntaje_evaluacion=%s, fecha_actualizacion=NOW(), activo={activo_value}
                    WHERE id_postulacion=%s
                ''', (self.estado, self.fuente_reclutamiento, self.notas, 
                      self.puntaje_evaluacion, self.id_postulacion))
                return self.id_postulacion
            else:
                # Usar valor boolean correcto según tipo de BD
                if db.db_type == 'postgresql':
                    activo_value = 'TRUE' if self.activo else 'FALSE'
                else:
                    activo_value = 1 if self.activo else 0
                cursor.execute(f'''
                    INSERT INTO postulaciones (cedula, id_cargo, estado, 
                    fuente_reclutamiento, notas, puntaje_evaluacion, activo)
                    VALUES (%s, %s, %s, %s, %s, %s, {activo_value})
                ''', (self.cedula, self.id_cargo, self.estado,
                      self.fuente_reclutamiento, self.notas, self.puntaje_evaluacion))
                return cursor.lastrowid
    
    def delete(self) -> bool:
        """Eliminar la postulación de la base de datos"""
        if not self.id_postulacion:
            return False
            
        with db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('DELETE FROM postulaciones WHERE id_postulacion = %s', 
                           (self.id_postulacion,))
                return cursor.rowcount > 0
            except Exception as e:
                print(f"Error al eliminar postulación: {e}")
                return False
    
    @classmethod
    def get_by_id(cls, id_postulacion: int) -> Optional['Postulacion']:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM postulaciones WHERE id_postulacion = %s', (id_postulacion,))
            row = cursor.fetchone()
            if row:
                postulacion = cls.from_row(row)
                # Cargar candidato relacionado
                postulacion.candidato = Candidato.get_by_cedula(postulacion.cedula)
                # Cargar cargo relacionado
                postulacion.cargo = Cargo.get_by_id(postulacion.id_cargo)
                return postulacion
            return None
    
    @classmethod
    def get_por_candidato(cls, cedula: str) -> List['Postulacion']:
        """Obtener todas las postulaciones de un candidato específico"""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p.* FROM postulaciones p
                WHERE p.cedula = %s
                ORDER BY p.fecha_postulacion DESC
            ''', (cedula,))
            
            postulaciones = []
            for row in cursor.fetchall():
                postulacion = cls.from_row(row)
                # Cargar candidato relacionado
                postulacion.candidato = Candidato.get_by_cedula(postulacion.cedula)
                # Cargar cargo relacionado
                postulacion.cargo = Cargo.get_by_id(postulacion.id_cargo)
                postulaciones.append(postulacion)
            
            return postulaciones
    
    @classmethod
    def get_all(cls, estado: Optional[str] = None, page: int = 1, per_page: int = 10) -> List['Postulacion']:
        """Obtener todas las postulaciones con paginación"""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Construir consulta base
            # Solo filtrar por candidato activo (p.activo no existe en postulaciones)
            from models import get_active_value
            activo_value = get_active_value()
            query = f'''
                SELECT p.* FROM postulaciones p
                JOIN candidatos c ON p.cedula = c.cedula
                WHERE c.activo = {activo_value}
            '''
            params = []
            
            # Agregar filtro por estado si se especifica
            if estado:
                query += ' AND p.estado = %s'
                params.append(estado)
            
            # Agregar ordenamiento
            query += ' ORDER BY p.fecha_postulacion DESC'
            
            # Agregar paginación
            offset = (page - 1) * per_page
            query += ' LIMIT %s OFFSET %s'
            params.extend([per_page, offset])
            
            cursor.execute(query, params)
            
            postulaciones = []
            for row in cursor.fetchall():
                postulacion = cls.from_row(row)
                # Cargar candidato relacionado
                postulacion.candidato = Candidato.get_by_cedula(postulacion.cedula)
                # Cargar cargo relacionado
                postulacion.cargo = Cargo.get_by_id(postulacion.id_cargo)
                postulaciones.append(postulacion)
            return postulaciones
    
    @classmethod
    def get_total_count(cls, estado: Optional[str] = None) -> int:
        """Obtener el total de postulaciones para paginación"""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Solo filtrar por candidato activo (p.activo no existe en postulaciones)
            activo_value = get_active_value()
            query = f'''
                SELECT COUNT(*) as total FROM postulaciones p
                JOIN candidatos c ON p.cedula = c.cedula
                WHERE c.activo = {activo_value}
            '''
            params = []
            
            if estado:
                query += ' AND p.estado = %s'
                params.append(estado)
            
            cursor.execute(query, params)
            result = cursor.fetchone()
            return result['total'] if result else 0
    
    @classmethod
    def get_desactivadas(cls, page: int = 1, per_page: int = 10) -> List['Postulacion']:
        """Obtener postulaciones desactivadas con paginación"""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Solo filtrar por candidato activo (p.activo no existe en postulaciones)
            activo_true = get_active_value()
            query = f'''
                SELECT p.* FROM postulaciones p
                JOIN candidatos c ON p.cedula = c.cedula
                WHERE c.activo = {activo_true}
                ORDER BY p.fecha_postulacion DESC
            '''
            
            # Agregar paginación
            offset = (page - 1) * per_page
            query += ' LIMIT %s OFFSET %s'
            
            cursor.execute(query, [per_page, offset])
            
            postulaciones = []
            for row in cursor.fetchall():
                postulacion = cls.from_row(row)
                # Cargar candidato relacionado
                postulacion.candidato = Candidato.get_by_cedula(postulacion.cedula)
                # Cargar cargo relacionado
                postulacion.cargo = Cargo.get_by_id(postulacion.id_cargo)
                postulaciones.append(postulacion)
            return postulaciones
    
    @classmethod
    def get_total_desactivadas(cls) -> int:
        """Obtener el total de postulaciones desactivadas para paginación"""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Solo filtrar por candidato activo (p.activo no existe en postulaciones)
            activo_true = get_active_value()
            query = f'''
                SELECT COUNT(*) as total FROM postulaciones p
                JOIN candidatos c ON p.cedula = c.cedula
                WHERE c.activo = {activo_true}
            '''
            
            cursor.execute(query)
            result = cursor.fetchone()
            return result['total'] if result else 0
    
    @classmethod
    def get_por_cargo(cls, cargo_id: int) -> List['Postulacion']:
        """Obtener todas las postulaciones para un cargo específico"""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            # Usar helper para valor boolean según tipo de BD
            activo_value = get_active_value()
            cursor.execute(f'''
                SELECT p.* FROM postulaciones p
                JOIN candidatos c ON p.cedula = c.cedula
                WHERE p.id_cargo = %s AND c.activo = {activo_value}
                ORDER BY p.fecha_postulacion DESC
            ''', (cargo_id,))
            
            postulaciones = []
            for row in cursor.fetchall():
                postulacion = cls.from_row(row)
                # Cargar candidato relacionado
                postulacion.candidato = Candidato.get_by_cedula(postulacion.cedula)
                # Cargar cargo relacionado
                postulacion.cargo = Cargo.get_by_id(postulacion.id_cargo)
                postulaciones.append(postulacion)
            return postulaciones
    
    

@dataclass
class Referencia:
    id: Optional[int] = None
    cedula: str = ""
    nombre: str = ""
    telefono: str = ""
    relacion: str = "Amigo"
    descripcion: str = "No aplica"
    
    @classmethod
    def from_row(cls, row: Dict) -> 'Referencia':
        return cls(
            id=row.get('id'),
            cedula=row.get('cedula', ''),
            nombre=row.get('nombre', ''),
            telefono=row.get('telefono', ''),
            relacion=row.get('relacion', 'Amigo'),
            descripcion=row.get('descripcion', 'No aplica')
        )
    
    def save(self) -> int:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            if self.id:
                cursor.execute('''
                    UPDATE referencias_personales SET 
                    nombre=%s, telefono=%s, relacion=%s, descripcion=%s 
                    WHERE id=%s
                ''', (self.nombre, self.telefono, self.relacion,
                      self.descripcion, self.id))
                return self.id
            else:
                cursor.execute('''
                    INSERT INTO referencias_personales 
                    (cedula, nombre, telefono, relacion, descripcion)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (self.cedula, self.nombre, 
                      self.telefono, self.relacion, self.descripcion))
                return cursor.lastrowid


@dataclass
class Experiencia:
    id_experiencia: Optional[int] = None
    cedula: str = ""
    empresa: str = ""
    cargo: str = ""
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    actual: bool = False
    descripcion: str = ""
    
    @classmethod
    def from_row(cls, row: Dict) -> 'Experiencia':
        fecha_inicio = row.get('fecha_inicio')
        if fecha_inicio and isinstance(fecha_inicio, str):
            try:
                fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            except ValueError:
                fecha_inicio = None
        
        fecha_fin = row.get('fecha_fin')
        if fecha_fin and isinstance(fecha_fin, str):
            try:
                fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
            except ValueError:
                fecha_fin = None
        
        return cls(
            id_experiencia=row.get('id_experiencia'),
            cedula=row.get('cedula', ''),
            empresa=row.get('empresa', ''),
            cargo=row.get('cargo', ''),
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            actual=bool(row.get('actual', False)),
            descripcion=row.get('descripcion', '')
        )
    
    def save(self) -> int:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            if self.id_experiencia:
                cursor.execute('''
                    UPDATE experiencias SET empresa=%s, cargo=%s, fecha_inicio=%s, 
                    fecha_fin=%s, actual=%s, descripcion=%s 
                    WHERE id_experiencia=%s
                ''', (self.empresa, self.cargo, self.fecha_inicio,
                      self.fecha_fin, self.actual, self.descripcion, self.id_experiencia))
                return self.id_experiencia
            else:
                cursor.execute('''
                    INSERT INTO experiencias 
                    (cedula, empresa, cargo, fecha_inicio, fecha_fin, actual, descripcion)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                ''', (self.cedula, self.empresa, self.cargo,
                      self.fecha_inicio, self.fecha_fin, self.actual, self.descripcion))
                return cursor.lastrowid


@dataclass
class EstadisticasRRHH:
    """Clase para estadísticas de RRHH"""
    
    @classmethod
    def get_dashboard_stats(cls) -> Dict[str, Any]:
        """Obtener estadísticas para el dashboard"""
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Cargos activos
                query = 'SELECT COUNT(*) as count FROM cargos WHERE estado = %s'
                params = ('Activo',)
                print(f"DEBUG SQL: {query} | params: {params}")
                cursor.execute(query, params)
                result = cursor.fetchone()
                cargos_activos = result['count'] if isinstance(result, dict) else result[0]
                
                # Total candidatos
                cursor.execute(f'SELECT COUNT(*) as count FROM candidatos WHERE activo = {get_active_value()}')
                result = cursor.fetchone()
                total_candidatos = result['count'] if isinstance(result, dict) else result[0]
                
                # Candidatos activos
                cursor.execute(f'SELECT COUNT(*) as count FROM candidatos WHERE activo = {get_active_value()}')
                result = cursor.fetchone()
                candidatos_activos = result['count'] if isinstance(result, dict) else result[0]
                
                # Total postulaciones
                cursor.execute('SELECT COUNT(*) as count FROM postulaciones')
                result = cursor.fetchone()
                total_postulaciones = result['count'] if isinstance(result, dict) else result[0]
                
                # Postulaciones por estado
                cursor.execute('''
                    SELECT estado, COUNT(*) as total 
                    FROM postulaciones 
                    GROUP BY estado
                ''')
                por_estado = {row['estado']: row['total'] for row in cursor.fetchall()}
                
                # Postulaciones pendientes
                postulaciones_pendientes = por_estado.get('Recibido', 0) + por_estado.get('En revision', 0)
                
                # Total cargos
                cursor.execute('SELECT COUNT(*) as count FROM cargos')
                result = cursor.fetchone()
                total_cargos = result['count'] if isinstance(result, dict) else result[0]
                
                return {
                    'cargos_activos': cargos_activos,
                    'total_candidatos': total_candidatos,
                    'candidatos_activos': candidatos_activos,
                    'total_postulaciones': total_postulaciones,
                    'postulaciones_pendientes': postulaciones_pendientes,
                    'total_cargos': total_cargos,
                    'por_estado': por_estado
                }
        except Exception as e:
            print(f"Error en get_dashboard_stats: {e}")
            # Retornar valores por defecto si hay error
            return {
                'cargos_activos': 0,
                'total_candidatos': 0,
                'candidatos_activos': 0,
                'total_postulaciones': 0,
                'postulaciones_pendientes': 0,
                'total_cargos': 0,
                'por_estado': {}
            }


@dataclass
class EstadoPipeline:
    id_estado: int = 0
    codigo: str = ""
    descripcion: str = ""
    
    @classmethod
    def from_row(cls, row: Dict) -> 'EstadoPipeline':
        return cls(
            id_estado=row.get('id_estado', 0),
            codigo=row.get('codigo', ''),
            descripcion=row.get('descripcion', '')
        )
    
    @classmethod
    def get_all(cls) -> List['EstadoPipeline']:
        """Obtener todos los estados del pipeline desde la base de datos"""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM cat_estado_postulacion ORDER BY id_estado')
            return [cls.from_row(row) for row in cursor.fetchall()]
    
    @classmethod
    def get_by_codigo(cls, codigo: str) -> Optional['EstadoPipeline']:
        """Obtener un estado por su código"""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM cat_estado_postulacion WHERE codigo = %s', (codigo,))
            row = cursor.fetchone()
            return cls.from_row(row) if row else None
    
    @classmethod
    def get_siguientes_estados(cls, estado_actual: str) -> List[str]:
        """Obtener los siguientes estados válidos desde la base de datos"""
        # Transiciones válidas basadas en el pipeline de reclutamiento
        # Usando los nombres corregidos sin tildes de la base de datos
        transiciones = {
            'Recibido': ['En revision', 'Rechazado', 'Descartado'],
            'En revision': ['Entrevista tecnica', 'Rechazado', 'Descartado'],
            'Entrevista tecnica': ['Entrevista RRHH', 'Rechazado', 'Descartado'],
            'Entrevista RRHH': ['Oferta', 'Rechazado', 'Descartado'],
            'Oferta': ['Contratado', 'Rechazado'],
            'Contratado': [],
            'Rechazado': [],
            'Descartado': []
        }
        return transiciones.get(estado_actual, [])
    
    @classmethod
    def puede_transicionar(cls, estado_actual: str, nuevo_estado: str) -> bool:
        """Verificar si se puede transicionar de un estado a otro"""
        return nuevo_estado in cls.get_siguientes_estados(estado_actual)
