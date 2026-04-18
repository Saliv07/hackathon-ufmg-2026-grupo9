#!/bin/bash

# Script para rodar Backend, Dashboard de Monitoramento e Frontend simultaneamente (Linux/macOS)

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Iniciando plataforma jurídica do Grupo 9..."

# 1. Backend Setup (porta 5000)
echo "[1/3] Configuração e Inicialização do Backend"
cd "$ROOT_DIR/backend"
python3 -m venv venv
./venv/bin/python -m pip install -r requirements.txt
./venv/bin/python main.py &
BACKEND_PID=$!

# 2. Dashboard de Monitoramento - Streamlit (porta 8501)
echo "[2/3] Configuração e Inicialização do Monitoramento"
cd "$ROOT_DIR"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
./venv/bin/python -m pip install --quiet -r requirements.txt

if [ ! -f "data/processed/casos_60k.parquet" ]; then
    echo "  Gerando artefatos de dados..."
    ./venv/bin/python -m src.monitor.load_data
    ./venv/bin/python -m src.monitor.baseline
    ./venv/bin/python -m src.monitor.gerar_sintetico
fi

./venv/bin/python -m streamlit run src/monitor/dashboards/app.py \
    --server.port 8501 \
    --server.headless true \
    --browser.gatherUsageStats false &
STREAMLIT_PID=$!

# 3. Frontend Setup - foreground (porta 5173)
echo "[3/3] Configuração e Inicialização do Frontend"
cd "$ROOT_DIR/frontend"
npm install
npm run dev

# Quando o frontend for encerrado, mata os processos auxiliares
trap "kill $BACKEND_PID $STREAMLIT_PID 2>/dev/null" EXIT
