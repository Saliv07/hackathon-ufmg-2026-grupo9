# Processo único: Flask + Dash + frontend estático, tudo em :5000.
# Windows PowerShell
#
# Topologia:
#   http://localhost:5000/                  -> frontend React (build estático)
#   http://localhost:5000/api/*             -> endpoints Flask
#   http://localhost:5000/monitoramento/    -> Dash app (montado no mesmo Flask)

$rootDir = $PSScriptRoot
New-Item -ItemType Directory -Force -Path "$rootDir\logs" | Out-Null

Write-Host "Iniciando plataforma jurídica do Grupo 9 (processo único)..." -ForegroundColor Cyan

# 1. Build do frontend
Write-Host "[1/3] Build do frontend" -ForegroundColor Yellow
Set-Location "$rootDir\frontend"
npm install --silent
npm run build

# 2. Backend venv + deps
Write-Host "[2/3] Preparando backend venv" -ForegroundColor Yellow
Set-Location "$rootDir\backend"
if (-not (Test-Path "venv")) {
    python -m venv venv
}
.\venv\Scripts\python -m pip install --quiet --upgrade pip
.\venv\Scripts\python -m pip install --quiet -r requirements.txt

# 3. Gerar artefatos do monitoramento se faltarem
$parquet60k = "$rootDir\data\processed\casos_60k.parquet"
$parquetEnr = "$rootDir\data\processed\casos_enriquecidos.parquet"
if (-not (Test-Path $parquet60k) -or -not (Test-Path $parquetEnr)) {
    Write-Host "  Gerando artefatos de dados..." -ForegroundColor Gray
    Set-Location $rootDir
    .\backend\venv\Scripts\python -m src.monitor.load_data
    .\backend\venv\Scripts\python -m src.monitor.baseline
    .\backend\venv\Scripts\python -m src.monitor.gerar_sintetico
    if (Test-Path "$rootDir\artefatos\modelo_xgboost.pkl") {
        .\backend\venv\Scripts\python -m src.monitor.politica_xgboost
    }
}

# 4. Sobe Flask (com Dash embutido)
Write-Host "[3/3] Servidor Flask + Dash (exposto :5000)" -ForegroundColor Yellow
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Acesse:   http://localhost:5000/" -ForegroundColor Green
Write-Host "  API:      http://localhost:5000/api/" -ForegroundColor Green
Write-Host "  Monitor:  http://localhost:5000/monitoramento/" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Set-Location "$rootDir\backend"
.\venv\Scripts\python main.py
