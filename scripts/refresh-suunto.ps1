$ErrorActionPreference = "Stop"

$mcpProcesses = Get-CimInstance Win32_Process -Filter "Name = 'mcpSuunto-server.exe'"

foreach ($process in $mcpProcesses) {
    Write-Host "Arrêt du serveur MCP (PID $($process.ProcessId))..."
    Stop-Process -Id $process.ProcessId -Force
}

if (-not $mcpProcesses) {
    Write-Host "Aucun serveur mcpSuunto-server actif."
}

Start-Sleep -Seconds 2

Write-Host "Import des nouvelles activités..."
& uv run mcpSuunto @args
exit $LASTEXITCODE
