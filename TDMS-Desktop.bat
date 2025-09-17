@echo off
cd /d "%~dp0"

echo ========================================
echo    TDMS Desktop Application Launcher
echo ========================================
echo.

REM Check if virtual environment exists, if not create it
if not exist "venv\Scripts\python.exe" (
    echo Setting up virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Error: Failed to create virtual environment
        echo Make sure Python is installed and in PATH
        pause
        exit /b 1
    )
    echo Virtual environment created successfully!
)

REM Activate virtual environment and install/update dependencies
echo Checking dependencies...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo Warning: Could not activate virtual environment, using direct path
    set PYTHON_CMD=venv\Scripts\python.exe
    set PIP_CMD=venv\Scripts\pip.exe
) else (
    set PYTHON_CMD=python
    set PIP_CMD=pip
)

REM Install/update required packages
echo Installing/updating dependencies...
%PIP_CMD% install --upgrade pip > nul 2>&1
%PIP_CMD% install fastapi[all] pywebview python-dotenv > nul 2>&1

if errorlevel 1 (
    echo Warning: Some dependencies may not have installed correctly
    echo Attempting to start application anyway...
)

echo.
echo Starting TDMS Desktop Application...
echo Using virtual environment Python

REM Start the application
%PYTHON_CMD% -m src.desktop.simple_app

if errorlevel 1 (
    echo.
    echo ========================================
    echo Error: Failed to start TDMS Desktop Application
    echo ========================================
    echo.
    echo Troubleshooting:
    echo 1. Make sure Python 3.7+ is installed
    echo 2. Check if all files are present in the project directory
    echo 3. Try running setup_environment.bat first
    echo.
    echo Dependencies that should be installed:
    echo   - fastapi[all]
    echo   - pywebview  
    echo   - python-dotenv
    echo.
    echo Environment variables needed in .env:
    echo   - DESKTOP_GOOGLE_OAUTH_CLIENT_ID
    echo   - DESKTOP_GOOGLE_OAUTH_CLIENT_SECRET
    echo.
    pause
    exit /b 1
)

echo.
echo Application closed successfully.
pause



