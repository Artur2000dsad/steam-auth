@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo ===============================================
echo   Steam Auth Server Bootstrap and Start
echo ===============================================
echo.

set "PYTHON_CMD="

where py >nul 2>&1
if not errorlevel 1 (
    py -3 --version >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=py -3"
)

if not defined PYTHON_CMD (
    where python >nul 2>&1
    if not errorlevel 1 (
        python --version >nul 2>&1
        if not errorlevel 1 set "PYTHON_CMD=python"
    )
)

if not defined PYTHON_CMD (
    echo [INFO] Python not found. Trying to install via winget...
    where winget >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] winget is not available on this system.
        echo [ERROR] Install Python 3.11+ manually and rerun this file.
        echo [ERROR] https://www.python.org/downloads/windows/
        pause
        exit /b 1
    )

    winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
    if errorlevel 1 (
        echo [ERROR] Failed to install Python using winget.
        pause
        exit /b 1
    )

    set "PYTHON_CMD=py -3"
    %PYTHON_CMD% --version >nul 2>&1
    if errorlevel 1 (
        set "PYTHON_CMD=python"
    )
)

echo [INFO] Using Python command: %PYTHON_CMD%

if not exist ".venv\" (
    echo [INFO] Creating virtual environment...
    %PYTHON_CMD% -m venv ".venv"
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

set "VENV_PY=.venv\Scripts\python.exe"
if not exist "%VENV_PY%" (
    echo [ERROR] Virtual environment Python not found: %VENV_PY%
    pause
    exit /b 1
)

echo [INFO] Upgrading pip...
"%VENV_PY%" -m pip install --upgrade pip
if errorlevel 1 (
    echo [WARN] pip upgrade failed, continuing...
)

if exist "requirements.txt" (
    echo [INFO] Installing dependencies from requirements.txt...
    "%VENV_PY%" -m pip install -r "requirements.txt"
    if errorlevel 1 (
        echo [ERROR] Dependency installation failed.
        pause
        exit /b 1
    )
) else (
    echo [INFO] requirements.txt not found, installing minimal packages...
    "%VENV_PY%" -m pip install Flask psutil pycryptodome
    if errorlevel 1 (
        echo [ERROR] Dependency installation failed.
        pause
        exit /b 1
    )
)

if not exist "steam_auth_server.py" (
    echo [ERROR] steam_auth_server.py not found in:
    echo         %SCRIPT_DIR%
    pause
    exit /b 1
)

echo.
echo [INFO] Starting Steam Auth Server...
echo.
"%VENV_PY%" "steam_auth_server.py"
set "EXIT_CODE=%ERRORLEVEL%"

echo.
echo [INFO] Server stopped with code %EXIT_CODE%.
pause
exit /b %EXIT_CODE%
