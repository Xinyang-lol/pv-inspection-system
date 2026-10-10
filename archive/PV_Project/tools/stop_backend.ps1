param(
    [string]$WorkingDirectory = (Split-Path -Parent $PSScriptRoot)
)

$runtimeDir = Join-Path $WorkingDirectory "backend\runtime"
$pidPath = Join-Path $runtimeDir "server.pid"

if (Test-Path -LiteralPath $pidPath) {
    $pidValue = Get-Content -LiteralPath $pidPath | Select-Object -First 1
    if ($pidValue) {
        try {
            Stop-Process -Id ([int]$pidValue) -Force -ErrorAction Stop
            Remove-Item -LiteralPath $pidPath -Force -ErrorAction SilentlyContinue
            Write-Output ("stopped:" + $pidValue)
            exit 0
        } catch {
            Remove-Item -LiteralPath $pidPath -Force -ErrorAction SilentlyContinue
        }
    }
}

$targets = Get-CimInstance Win32_Process | Where-Object {
    $_.Name -eq "python.exe" -and $_.CommandLine -like "*-m backend.app*"
}

foreach ($target in $targets) {
    try {
        Stop-Process -Id $target.ProcessId -Force -ErrorAction Stop
        Write-Output ("stopped:" + $target.ProcessId)
    } catch {
    }
}
