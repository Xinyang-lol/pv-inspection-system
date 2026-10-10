@echo off
cd /d "%~dp0"
python -m venv .venv
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install -r backend\requirements.txt
if errorlevel 1 goto failed
echo Installation complete. Open http://127.0.0.1:5000 after starting the backend.
pause
exit /b 0
:failed
echo Installation failed. Check Python and network access, then retry.
pause
exit /b 1
