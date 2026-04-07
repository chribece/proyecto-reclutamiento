@echo off
set FLASK_ENV=testing
set SECRET_KEY=test123
echo Iniciando aplicación Flask con SQLite...
echo FLASK_ENV: %FLASK_ENV%
echo SECRET_KEY: %SECRET_KEY%
.\venv\Scripts\python.exe app.py
pause
