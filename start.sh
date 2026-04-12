#!/bin/bash

# Script de inicio para Render
# Inicializa la base de datos y luego inicia la aplicación

echo " Iniciando aplicación Flask en Render..."

# Inicializar base de datos si es necesario
if [ "$FLASK_ENV" = "production" ]; then
    echo " Inicializando base de datos de producción..."
    python init_produccion.py
    echo " Base de datos inicializada"
fi

# Iniciar Gunicorn con el puerto de Render
echo " Iniciando Gunicorn en puerto $PORT..."
exec gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --access-logfile - --error-logfile -
