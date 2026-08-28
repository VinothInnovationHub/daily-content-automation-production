$ErrorActionPreference = "Stop"
if (-not (Test-Path ".venv")) {
    py -3.12 -m venv .venv
}
. .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
if (-not (Test-Path ".env")) {
    Copy-Item .env.example .env
}
Write-Host "Local environment ready."
Write-Host "Start with: uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000"
