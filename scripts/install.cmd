@echo off
setlocal
cd /d "%~dp0.."
python -m venv .venv
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
echo Dependencies installed. Run scripts/start.cmd to start the server.
pause
exit /b 0
:failed
echo Installation failed. Check Python and package download access.
pause
exit /b 1
