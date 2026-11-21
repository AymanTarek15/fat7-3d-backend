@echo off
REM One-time local setup for the FATH Django backend on a new machine.
REM Creates a virtual environment, installs the dependencies, writes a local
REM .env and builds the SQLite database. Safe to re-run: nothing already in
REM place is overwritten.

cd /d "%~dp0"

echo.
echo === FATH backend setup ===
echo.

echo [1/4] Virtual environment
if exist ".venv\Scripts\python.exe" (
    echo       .venv already exists - reusing it.
) else (
    python -m venv .venv
    if errorlevel 1 (
        echo       Could not create .venv. Is Python 3 installed and on PATH?
        exit /b 1
    )
    echo       Created .venv
)

set "VENV_PY=%~dp0.venv\Scripts\python.exe"

echo.
echo [2/4] Dependencies
"%VENV_PY%" -m pip install --upgrade pip --quiet
"%VENV_PY%" -m pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo       Installing from requirements.txt failed.
    exit /b 1
)
echo       Installed from requirements.txt

echo.
echo [3/4] Local .env
"%VENV_PY%" scripts\make_dev_env.py
if errorlevel 1 (
    echo       Could not write .env.
    exit /b 1
)

echo.
echo [4/4] Database
"%VENV_PY%" manage.py migrate
if errorlevel 1 (
    echo       Migrations failed.
    exit /b 1
)

echo.
echo === Done ===
echo.
echo Next steps:
echo   1. Create an admin login:  .venv\Scripts\python manage.py createsuperuser
echo   2. Start the API:          run-backend.cmd
echo   3. In the frontend repo, create .env.local containing:
echo        NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000
echo        DJANGO_API_BASE=http://127.0.0.1:8000
echo      then run:  npm install  and  npm run dev
echo.
