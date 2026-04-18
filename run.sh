#!/bin/bash

# Gateway unificado: porta 8080 serve frontend, backend e monitoramento
# Linux/macOS
#
# Topologia:
#   http://localhost:8080/                  -> frontend React (build estático)
#   http://localhost:8080/api/*             -> backend Flask (interno :5000)
#   http://localhost:8080/monitoramento/*   -> dashboard Streamlit (interno :8501)
#
# Para desenvolvimento com hot-reload, use ./dev.sh

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$ROOT_DIR/logs"

echo "Iniciando plataforma jurídica do Grupo 9..."

# 1. Verificar Caddy
if [ ! -x "$ROOT_DIR/bin/caddy" ]; then
    echo "Caddy não encontrado em ./bin/caddy — baixando..."
    mkdir -p "$ROOT_DIR/bin"
    curl -L -o /tmp/caddy.tar.gz "https://github.com/caddyserver/caddy/releases/download/v2.10.2/caddy_2.10.2_linux_amd64.tar.gz"
    tar xzf /tmp/caddy.tar.gz -C "$ROOT_DIR/bin" caddy
    chmod +x "$ROOT_DIR/bin/caddy"
    rm /tmp/caddy.tar.gz
fi

# 2. Build do frontend (produção)
echo "[1/4] Build do frontend"
cd "$ROOT_DIR/frontend"
npm install --silent
npm run build

# 3. Backend Flask (interno :5000)
echo "[2/4] Backend Flask (interno :5000)"
cd "$ROOT_DIR/backend"
python3 -m venv venv 2>/dev/null
./venv/bin/python -m pip install --quiet -r requirements.txt
./venv/bin/python main.py > "$ROOT_DIR/logs/backend.log" 2>&1 &
BACKEND_PID=$!

# 4. Streamlit (interno :8501, com baseUrlPath /monitoramento)
echo "[3/4] Dashboard Streamlit (interno :8501)"
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
    --server.port 8501 > "$ROOT_DIR/logs/streamlit.log" 2>&1 &
STREAMLIT_PID=$!

# 5. Caddy gateway (exposto :8080, foreground)
echo "[4/4] Gateway Caddy (exposto :8080)"
echo ""
echo "============================================"
echo "  Acesse: http://localhost:8080/"
echo "  API:    http://localhost:8080/api/"
echo "  Monitor: http://localhost:8080/monitoramento/"
echo "============================================"
echo ""

trap "kill $BACKEND_PID $STREAMLIT_PID 2>/dev/null" EXIT
"$ROOT_DIR/bin/caddy" run --config "$ROOT_DIR/Caddyfile"
