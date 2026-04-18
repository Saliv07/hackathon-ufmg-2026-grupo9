# Script para rodar Backend e Frontend simultaneamente (Windows PowerShell)

Write-Host "Iniciando plataforma jurídica do Grupo 9..." -ForegroundColor Cyan

# 1. Iniciar Backend em uma nova janela
Write-Host "[1/2] Iniciando Backend Python (Flask)..." -ForegroundColor Yellow
$backendCommand = "cd backend; python -m venv venv; .\venv\Scripts\activate; pip install -r requirements.txt; python main.py"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "$backendCommand" -WindowStyle Normal

# 2. Iniciar Frontend na janela atual
Write-Host "[2/2] Iniciando Frontend React (Vite)..." -ForegroundColor Yellow
cd frontend
npm install
npm run dev
