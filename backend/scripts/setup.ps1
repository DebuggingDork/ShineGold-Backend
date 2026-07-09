# Run from backend/ folder:
#   powershell -ExecutionPolicy Bypass -File scripts/setup.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

if (-not (Test-Path ".env")) {
    Write-Error ".env missing. Copy .env.example to .env and fill Supabase + JWT values."
}

Write-Host "==> Installing dependencies..."
uv sync

Write-Host "==> Running migrations..."
uv run alembic upgrade head

Write-Host "==> Seeding admin + executives..."
uv run python scripts/seed_admin.py
uv run python scripts/seed_executives.py

Write-Host ""
Write-Host "Setup complete. Start API with:"
Write-Host "  uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
Write-Host ""
Write-Host "Login: ADMIN001 / ChangeMe123!  or  EXEC001 / ChangeMe123!"
