#!/bin/bash

# Script para rodar Backend e Frontend simultaneamente (Linux/macOS)

echo "Iniciando plataforma jurídica do Grupo 9..."

# 1. Backend Setup
echo "[1/2] Configuração e Inicialização do Backend"
cd backend
python3 -m venv venv
./venv/bin/python -m pip install -r requirements.txt
./venv/bin/python main.py &
BACKEND_PID=$!
cd ..

# 2. Frontend Setup
echo "[2/2] Configuração e Inicialização do Frontend"
cd frontend
npm install
npm run dev

# Quando o frontend for encerrado, mata o processo do backend
trap "kill $BACKEND_PID" EXIT
