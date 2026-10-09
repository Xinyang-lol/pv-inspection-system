@echo off
setlocal
cd /d "%~dp0.."
if not exist "backend\services\pipeline.py" (
    echo Missing original backend/services/pipeline.py. See docs/source-status.md.
    pause
    exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found. Run scripts/install.cmd first.
    pause
    exit /b 1
)
echo Starting server. Default address: http://127.0.0.1:5000
echo Press Ctrl+C to stop.
".venv\Scripts\python.exe" -m backend.app
if errorlevel 1 pause
