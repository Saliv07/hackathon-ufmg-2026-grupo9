Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "🚀 Iniciando Plataforma Jurídica do Grupo 9..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

Write-Host "`n[1/4] Preparando o ambiente do Backend (Python)..." -ForegroundColor Yellow
$backendCommand = "cd backend; python -m venv venv; Write-Host '[2/4] Instalando dependências do Backend...' -ForegroundColor Yellow; .\venv\Scripts\activate; pip install -r requirements.txt; Write-Host '[3/4] Iniciando o Backend...' -ForegroundColor Green; python main.py"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "$backendCommand" -WindowStyle Normal

Write-Host "`n[4/4] Preparando o ambiente do Frontend (Node.js)..." -ForegroundColor Yellow
Push-Location frontend
try {
    Write-Host "Instalando dependências do Frontend..." -ForegroundColor Yellow
    npm install
    Write-Host "`n✨ Tudo pronto! Iniciando o servidor Frontend..." -ForegroundColor Green
    Write-Host "👉 Acesse a URL gerada abaixo no seu navegador!" -ForegroundColor Green
    Write-Host "==================================================" -ForegroundColor Cyan
    npm run dev
} finally {
    Pop-Location
}