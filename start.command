#!/bin/bash
cd "$(dirname "$0")"

echo "======================================"
echo "      🚀 Iniciando Encontreras      "
echo "======================================"

echo "1. Comprobando Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python3 no está instalado."
    echo "Por favor, descárgalo e instálalo desde https://www.python.org/downloads/"
    echo "Presiona Enter para salir..."
    read
    exit 1
fi

if [ ! -d ".venv" ]; then
    echo "📦 Creando entorno virtual (esto puede tardar unos minutos la primera vez)..."
    python3 -m venv .venv
fi

source .venv/bin/activate

echo "⚙️  Verificando dependencias y navegadores..."
pip install -e . --quiet
playwright install chromium

echo "🤖 Iniciando procesos en segundo plano (Worker)..."
.venv/bin/huey_consumer src.core.tasks.huey > output/huey_bg.log 2>&1 &
HUEY_PID=$!

echo "🌐 Abriendo el Dashboard Web..."
sleep 2
# Soporte para Mac y Linux
if command -v open &> /dev/null; then
    open http://localhost:8888
elif command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:8888
fi

echo "✅ Servidor listo. Presiona CTRL+C en esta ventana para apagar Encontreras."
echo "--------------------------------------"
python main.py serve --reload

# Apagar el worker al cerrar el servidor principal
echo "Apagando procesos..."
kill $HUEY_PID
