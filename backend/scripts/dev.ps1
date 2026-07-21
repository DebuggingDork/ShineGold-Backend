# Start the ShineGold API the same way as `uv run fastapi dev` (port 8000).
# Run from backend/:
#   powershell -ExecutionPolicy Bypass -File scripts/dev.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

$port = 8000
$listeners = netstat -ano | Select-String "127.0.0.1:$port\s+.*LISTENING"
if ($listeners) {
    foreach ($line in $listeners) {
        $procId = ($line -split '\s+')[-1]
        if ($procId -match '^\d+$' -and $procId -ne '0') {
            Write-Error @"
Port $port is already in use (PID $procId).
Stop that process before starting the API, or Flutter will hit an outdated server.
Example: Stop-Process -Id $procId -Force
"@
        }
    }
}

$env:PYTHONUTF8 = "1"
$env:PORT = "$port"

Write-Host "Starting API on http://127.0.0.1:$port (fastapi dev) ..."
uv run fastapi dev
