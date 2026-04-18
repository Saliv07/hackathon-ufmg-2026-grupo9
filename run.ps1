# Script para rodar Backend, Dashboard de Monitoramento e Frontend simultaneamente (Windows PowerShell)

Write-Host "Iniciando plataforma jurídica do Grupo 9..." -ForegroundColor Cyan
$rootDir = $PSScriptRoot

# 1. Iniciar Backend em uma nova janela
Write-Host "[1/3] Iniciando Backend Python (Flask) na porta 5000..." -ForegroundColor Yellow
$backendCommand = "cd '$rootDir\backend'; python -m venv venv; .\venv\Scripts\activate; pip install -r requirements.txt; python main.py"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "$backendCommand" -WindowStyle Normal

# 2. Iniciar Dashboard de Monitoramento (Streamlit) em nova janela
Write-Host "[2/3] Iniciando Monitoramento (Streamlit) na porta 8501..." -ForegroundColor Yellow
$monitoringCommand = @"
cd '$rootDir';
if (-not (Test-Path venv)) { python -m venv venv };
.\venv\Scripts\activate;
pip install --quiet -r requirements.txt;
if (-not (Test-Path data\processed\casos_60k.parquet)) {
    Write-Host 'Gerando artefatos de dados...';
    python -m src.monitor.load_data;
    python -m src.monitor.baseline;
    python -m src.monitor.gerar_sintetico
};
python -m streamlit run src/monitor/dashboards/app.py --server.port 8501 --server.headless true --browser.gatherUsageStats false
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", "$monitoringCommand" -WindowStyle Normal

# 3. Iniciar Frontend na janela atual
Write-Host "[3/3] Iniciando Frontend React (Vite) na porta 5173..." -ForegroundColor Yellow
cd "$rootDir\frontend"
npm install
npm run dev
