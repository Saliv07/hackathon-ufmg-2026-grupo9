#!/bin/bash

# Modo DEV com hot-reload: usa Vite dev server em vez do build estático.
# Linux/macOS
#
# http://localhost:8080/                  -> proxy para Vite :5173 (hot-reload)
# http://localhost:8080/api/*             -> Flask (interno :5000)
# http://localhost:8080/monitoramento/*   -> Streamlit (interno :8501)

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$ROOT_DIR/logs"

if [ ! -x "$ROOT_DIR/bin/caddy" ]; then
    echo "Caddy não encontrado. Rode ./run.sh uma vez para baixar, ou baixe manualmente."
    exit 1
fi

# Caddyfile temporário com proxy pro Vite dev
cat > "$ROOT_DIR/Caddyfile.dev" <<EOF
:8080 {
    handle /api/* {
        reverse_proxy localhost:5000
    }
    handle /monitoramento/* {
        reverse_proxy localhost:8501
    }
    handle {
        reverse_proxy localhost:5173
    }
    log {
        output file ./logs/caddy.log
    }
}
EOF

# Backend
cd "$ROOT_DIR/backend"
./venv/bin/python main.py > "$ROOT_DIR/logs/backend.log" 2>&1 &
BACKEND_PID=$!

# Streamlit
cd "$ROOT_DIR"
./venv/bin/python -m streamlit run src/monitor/dashboards/app.py \
    --server.port 8501 > "$ROOT_DIR/logs/streamlit.log" 2>&1 &
STREAMLIT_PID=$!

# Vite dev
cd "$ROOT_DIR/frontend"
npm run dev -- --host 0.0.0.0 --port 5173 > "$ROOT_DIR/logs/vite.log" 2>&1 &
VITE_PID=$!

echo ""
echo "============================================"
echo "  DEV MODE — http://localhost:8080/"
echo "  Hot-reload ativo. Logs em ./logs/"
echo "============================================"
echo ""

trap "kill $BACKEND_PID $STREAMLIT_PID $VITE_PID 2>/dev/null; rm -f $ROOT_DIR/Caddyfile.dev" EXIT
"$ROOT_DIR/bin/caddy" run --config "$ROOT_DIR/Caddyfile.dev"
