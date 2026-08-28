$ErrorActionPreference = "Stop"
. .\.venv\Scripts\Activate.ps1
$env:LLM_PROVIDER="mock"
$env:ADMIN_TOKEN="test-token"
$env:CRON_SECRET="test-cron"
$env:DATABASE_URL="sqlite+aiosqlite:///./data/test.db"
python -m pytest -q
Write-Host "Basic local tests passed."
