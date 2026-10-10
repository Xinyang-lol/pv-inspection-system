@echo off
cd /d "%~dp0.."
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m backend.train_teacher_models --stage all --epochs 100 --device cpu --copy-best
) else (
    python -m backend.train_teacher_models --stage all --epochs 100 --device cpu --copy-best
)
if errorlevel 1 pause
