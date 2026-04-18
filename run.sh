#!/bin/bash
set -e

# Processo único: Flask + Dash + frontend estático, tudo em :5000.
# Linux/macOS
#
# Topologia:
#   http://localhost:5000/                  -> frontend React (build estático)
#   http://localhost:5000/api/*             -> endpoints Flask
#   http://localhost:5000/monitoramento/    -> Dash app (montado no mesmo Flask)

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$ROOT_DIR/logs"

echo "Iniciando plataforma jurídica do Grupo 9 (processo único)..."

# 1. Build do frontend (produção)
echo "[1/3] Build do frontend"
cd "$ROOT_DIR/frontend"
npm install --silent
npm run build

# 2. Backend venv + deps
echo "[2/3] Preparando backend venv"
cd "$ROOT_DIR/backend"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
./venv/bin/python -m pip install --quiet --upgrade pip
./venv/bin/python -m pip install --quiet -r requirements.txt

# 3. Gerar artefatos do monitoramento se faltarem
if [ ! -f "$ROOT_DIR/data/processed/casos_60k.parquet" ] || \
   [ ! -f "$ROOT_DIR/data/processed/casos_enriquecidos.parquet" ]; then
    echo "  Gerando artefatos de dados..."
    cd "$ROOT_DIR"
    ./backend/venv/bin/python -m src.monitor.load_data
    ./backend/venv/bin/python -m src.monitor.baseline
    ./backend/venv/bin/python -m src.monitor.gerar_sintetico
    if [ -f "artefatos/modelo_xgboost.pkl" ]; then
        ./backend/venv/bin/python -m src.monitor.politica_xgboost || true
    fi
fi

# 4. Sobe Flask (com Dash embutido)
echo "[3/3] Servidor Flask + Dash (exposto :5000)"
echo ""
echo "============================================"
echo "  Acesse:      http://localhost:5000/"
echo "  API:         http://localhost:5000/api/"
echo "  Monitor:     http://localhost:5000/monitoramento/"
echo "============================================"
echo ""
cd "$ROOT_DIR/backend"
exec ./venv/bin/python main.py
