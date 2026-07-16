# Windows dev startup orchestrator for SupplierGuard / ProcureAI
Write-Host "Starting SupplierGuard Services..." -ForegroundColor Green

# Ensure database exists/is seeded or ready before startup
if (-not (Test-Path "data/procureai.db")) {
    Write-Host "Database not found in data/. Initializing database..." -ForegroundColor Yellow
    .venv\Scripts\python -m scripts.seed_db
}

# Start backend in a new PowerShell console
Write-Host "Launching Backend (FastAPI)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$Host.UI.RawUI.WindowTitle = 'ProcureAI Backend'; Write-Host 'Starting Backend...'; `$env:PYTHONPATH='.'; .venv\Scripts\python backend/main.py"

# Start frontend in a new PowerShell console
Write-Host "Launching Frontend (Vite/React)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$Host.UI.RawUI.WindowTitle = 'ProcureAI Frontend'; cd frontend; npm run dev"

Write-Host "Both services are now starting in separate terminal windows." -ForegroundColor Green
