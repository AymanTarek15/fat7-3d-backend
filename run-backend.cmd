@echo off
REM Starts the FATH Django backend on http://127.0.0.1:8000
REM
REM This has to run from the backend directory: settings.py loads .env relative
REM to the working directory, so launching it from anywhere else falls back to
REM production settings and refuses to boot without DATABASE_URL. The cd below
REM uses this script's own folder, so it works wherever the repo is cloned.

cd /d "%~dp0"

if not exist ".env" (
    echo No .env found in this folder.
    echo Run setup-dev.cmd once first - it creates .env and the database.
    exit /b 1
)

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" manage.py runserver 8000
) else (
    python manage.py runserver 8000
)
