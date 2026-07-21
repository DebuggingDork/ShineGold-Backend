# Start the ShineGold API on port 8080 (matches Flutter AppConfig default).
# Run from backend/:
#   powershell -ExecutionPolicy Bypass -File scripts/dev.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

$port = 8080
$listeners = netstat -ano | Select-String "127.0.0.1:$port\s+.*LISTENING"
if ($listeners) {
    foreach ($line in $listeners) {
        $pid = ($line -split '\s+')[-1]
        if ($pid -match '^\d+$') {
            Write-Error @"
Port $port is already in use (PID $pid).
Stop that process before starting the API, or Flutter will hit an outdated server and new routes will 404.
Example: Stop-Process -Id $pid -Force
"@
        }
    }
}

Write-Host "Starting API on http://127.0.0.1:$port ..."
uv run fastapi dev --port $port
