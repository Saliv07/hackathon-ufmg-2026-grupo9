# Gateway unificado: porta 8080 serve frontend, backend e monitoramento
# Windows PowerShell
#
# Topologia:
#   http://localhost:8080/                  -> frontend React (build estático)
#   http://localhost:8080/api/*             -> backend Flask (interno :5000)
#   http://localhost:8080/monitoramento/*   -> dashboard Streamlit (interno :8501)

$rootDir = $PSScriptRoot
New-Item -ItemType Directory -Force -Path "$rootDir\logs" | Out-Null
New-Item -ItemType Directory -Force -Path "$rootDir\bin" | Out-Null

Write-Host "Iniciando plataforma jurídica do Grupo 9..." -ForegroundColor Cyan

# 1. Verificar Caddy
if (-not (Test-Path "$rootDir\bin\caddy.exe")) {
    Write-Host "Caddy não encontrado. Baixando..." -ForegroundColor Yellow
    $caddyUrl = "https://github.com/caddyserver/caddy/releases/download/v2.10.2/caddy_2.10.2_windows_amd64.zip"
    Invoke-WebRequest -Uri $caddyUrl -OutFile "$env:TEMP\caddy.zip"
    Expand-Archive -Path "$env:TEMP\caddy.zip" -DestinationPath "$rootDir\bin" -Force
    Remove-Item "$env:TEMP\caddy.zip"
}

# 2. Build do frontend
Write-Host "[1/4] Build do frontend" -ForegroundColor Yellow
Set-Location "$rootDir\frontend"
npm install --silent
npm run build

# 3. Backend Flask (em nova janela)
Write-Host "[2/4] Backend Flask (interno :5000)" -ForegroundColor Yellow
$backendCommand = "cd '$rootDir\backend'; if (-not (Test-Path venv)) { python -m venv venv }; .\venv\Scripts\activate; pip install --quiet -r requirements.txt; python main.py"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCommand -WindowStyle Minimized

# 4. Streamlit em nova janela
Write-Host "[3/4] Dashboard Streamlit (interno :8501)" -ForegroundColor Yellow
$monitoringCommand = @"
cd '$rootDir';
if (-not (Test-Path venv)) { python -m venv venv };
.\venv\Scripts\activate;
pip install --quiet -r requirements.txt;
if (-not (Test-Path data\processed\casos_60k.parquet)) {
    python -m src.monitor.load_data;
    python -m src.monitor.baseline;
    python -m src.monitor.gerar_sintetico
};
python -m streamlit run src/monitor/dashboards/app.py --server.port 8501
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $monitoringCommand -WindowStyle Minimized

# 5. Caddy gateway (foreground)
Write-Host "[4/4] Gateway Caddy (exposto :8080)" -ForegroundColor Yellow
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Acesse: http://localhost:8080/" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

Set-Location $rootDir
& "$rootDir\bin\caddy.exe" run --config "$rootDir\Caddyfile"
