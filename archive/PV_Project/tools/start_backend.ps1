param(
    [string]$PythonPath = "",
    [string]$WorkingDirectory = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = "Stop"
if (-not $PythonPath) {
    $PythonPath = Join-Path $WorkingDirectory ".venv\Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $PythonPath)) {
        $PythonPath = (Get-Command python -ErrorAction Stop).Source
    }
}

$runtimeDir = Join-Path $WorkingDirectory "backend\runtime"
if (-not (Test-Path -LiteralPath $runtimeDir)) {
    New-Item -ItemType Directory -Path $runtimeDir | Out-Null
}

$stdoutPath = Join-Path $runtimeDir "server.out.log"
$stderrPath = Join-Path $runtimeDir "server.err.log"
$pidPath = Join-Path $runtimeDir "server.pid"

$process = Start-Process `
    -FilePath $PythonPath `
    -ArgumentList "-m", "backend.app" `
    -WorkingDirectory $WorkingDirectory `
    -RedirectStandardOutput $stdoutPath `
    -RedirectStandardError $stderrPath `
    -WindowStyle Hidden `
    -PassThru

Set-Content -LiteralPath $pidPath -Value $process.Id -Encoding ascii
Write-Output $process.Id
