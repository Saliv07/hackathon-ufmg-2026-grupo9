#!/bin/bash

# Script para rodar Backend e Frontend simultaneamente (Linux/macOS)

echo "Iniciando plataforma jurídica do Grupo 9..."

# 1. Backend Setup
echo "[1/2] Configurando Backend (Python)..."
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt
# Inicia o backend em background
python3 main.py & 
BACKEND_PID=$!
cd ..

# 2. Frontend Setup
echo "[2/2] Configurando Frontend (Node.js)..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
fi

# Inicia o frontend (isso manterá o terminal ocupado)
npm run dev

# Quando o frontend for encerrado, mata o processo do backend
trap "kill $BACKEND_PID" EXIT
