from collections import defaultdict, deque, namedtuple
from typing import List, Dict, Any, Optional, Callable
from functools import wraps
from datetime import datetime, timedelta
import re

# Estructuras de datos optimizadas

class EstadoPipeline:
    """Máquina de estados para el pipeline de reclutamiento"""
    
    @classmethod
    def get_estados_disponibles(cls) -> List[str]:
        """Obtener todos los estados disponibles desde la base de datos"""
        from models import EstadoPipeline as EstadoModel
        estados = EstadoModel.get_all()
        return [estado.codigo for estado in estados]
    
    @classmethod
    def puede_transicionar(cls, estado_actual: str, nuevo_estado: str) -> bool:
        """Verificar si se puede transicionar de un estado a otro"""
        from models import EstadoPipeline as EstadoModel
        return EstadoModel.puede_transicionar(estado_actual, nuevo_estado)
    
    @classmethod
    def get_siguientes_estados(cls, estado_actual: str) -> List[str]:
        """Obtener los siguientes estados válidos"""
        from models import EstadoPipeline as EstadoModel
        return EstadoModel.get_siguientes_estados(estado_actual)


# Funciones utilitarias

def normalizar_texto(texto: str) -> str:
    """Normaliza texto para búsquedas"""
    if not texto:
        return ""
    texto = texto.lower().strip()
    texto = re.sub(r'[^\w\s]', '', texto)
    return texto


def calcular_match(candidato_habilidades: List[str], requisitos: List[str]) -> float:
    """Calcula porcentaje de match entre habilidades del candidato y requisitos"""
    if not requisitos:
        return 0.0
    
    candidato_set = set(normalizar_texto(h) for h in candidato_habilidades)
    requisitos_set = set(normalizar_texto(r) for r in requisitos)
    
    if not candidato_set:
        return 0.0
    
    matches = candidato_set.intersection(requisitos_set)
    return (len(matches) / len(requisitos_set)) * 100


def formatear_fecha(fecha: datetime) -> str:
    """Formatea fecha de manera amigable"""
    if not fecha:
        return "N/A"
    
    hoy = datetime.now()
    diff = hoy - fecha
    
    if diff.days == 0:
        return "Hoy"
    elif diff.days == 1:
        return "Ayer"
    elif diff.days < 7:
        return f"Hace {diff.days} días"
    elif diff.days < 30:
        semanas = diff.days // 7
        return f"Hace {semanas} semana{'s' if semanas > 1 else ''}"
    else:
        return fecha.strftime("%d/%m/%Y")


def validar_email(email: str) -> bool:
    """Validación robusta de email"""
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(patron, email) is not None


def generar_slug(texto: str) -> str:
    """Genera slug URL-friendly"""
    texto = normalizar_texto(texto)
    texto = re.sub(r'\s+', '-', texto)
    return texto[:50]


# Decoradores

def timer(func: Callable) -> Callable:
    """Mide tiempo de ejecución"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        inicio = datetime.now()
        resultado = func(*args, **kwargs)
        fin = datetime.now()
        print(f"⏱️ {func.__name__} tomó {(fin - inicio).total_seconds():.4f}s")
        return resultado
    return wrapper


def memoize(func: Callable) -> Callable:
    """Cache simple para funciones puras"""
    cache = {}
    @wraps(func)
    def wrapper(*args):
        if args not in cache:
            cache[args] = func(*args)
        return cache[args]
    return wrapper


# Named tuples para estructuras de datos ligeras
ResumenCandidato = namedtuple('ResumenCandidato', 
                             ['id', 'nombre', 'match_score', 'estado_postulacion'])

MetricasPipeline = namedtuple('MetricasPipeline',
                             ['total', 'por_estado', 'tiempo_promedio', 'tasa_conversion'])