@echo off
title Encontreras Local Server
cd /d "%~dp0"

echo ======================================
echo       🚀 Iniciando Encontreras      
echo ======================================

echo 1. Comprobando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no esta instalado o no esta en el PATH.
    echo Por favor descargalo desde https://www.python.org/downloads/
    echo Asegurate de marcar la casilla "Add python.exe to PATH" durante la instalacion.
    pause
    exit /b 1
)

if not exist ".venv\" (
    echo [NUEVO] Creando entorno virtual ^(esto puede tardar unos minutos la primera vez^)...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

echo 2. Verificando dependencias y navegadores asincronos...
pip install -e . --quiet
call playwright install chromium

echo 3. Iniciando procesos en segundo plano ^(Worker^)...
start /B "Huey Worker" .venv\Scripts\huey_consumer.exe src.core.tasks.huey > nul 2>&1

echo 4. Abriendo el Dashboard Web en tu navegador...
timeout /t 3 /nobreak > nul
start http://localhost:8888

echo ✅ Servidor listo. Presiona CTRL+C en esta ventana para apagar Encontreras.
echo --------------------------------------
python main.py serve --reload

echo.
echo Servidor detenido. Puedes cerrar esta ventana.
pause
