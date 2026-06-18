@echo off
setlocal ENABLEDELAYEDEXPANSION

title SABR RUST - Main Server + Steam Auth

echo ===============================================
echo   SABR RUST - Main Server + Steam Auth
echo ===============================================
echo.

cd /d "%~dp0"
if errorlevel 1 (
    echo [ERROR] Cannot open script folder
    pause
    exit /b 1
)

set "HTTP_PROXY="
set "HTTPS_PROXY="
set "ALL_PROXY="
set "http_proxy="
set "https_proxy="
set "all_proxy="
set "NO_PROXY=*"
set "no_proxy=*"

set "VENV_PY="
set "PARENT_VENV=..\.venv\Scripts\python.exe"

if exist ".venv\Scripts\python.exe" (
    set "VENV_PY=.venv\Scripts\python.exe"
)

if not defined VENV_PY (
    where python >nul 2>nul
    if errorlevel 1 (
        set "PYTHON_CMD=py -3"
    ) else (
        set "PYTHON_CMD=python"
    )
    echo [INFO] Creating local venv...
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create venv
        pause
        exit /b 1
    )
    set "VENV_PY=.venv\Scripts\python.exe"
)

if not exist "%VENV_PY%" (
    if exist "%PARENT_VENV%" (
        set "VENV_PY=%PARENT_VENV%"
        echo [INFO] Using parent venv
    )
)

if not exist "%VENV_PY%" (
    echo [ERROR] Python not found
    pause
    exit /b 1
)

"%VENV_PY%" -c "import flask" 2>nul
if errorlevel 1 (
    echo [INFO] Installing Flask...
    "%VENV_PY%" bootstrap_deps.py
    if errorlevel 1 (
        echo [ERROR] bootstrap_deps.py failed
        pause
        exit /b 1
    )
)

echo.
echo [INFO] Starting main_server.py
echo [INFO] Edit config.json for domain and launcher_server_url
echo.
"%VENV_PY%" main_server.py
set "EXIT_CODE=%ERRORLEVEL%"

echo.
echo [INFO] Stopped with code %EXIT_CODE%
pause
exit /b %EXIT_CODE%
