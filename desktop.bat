@echo off
cd /d "%~dp0"

echo ========================================
echo    TDMS Desktop Application Launcher
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo ❌ Virtual environment not found!
    echo.
    echo Please run setup_env.bat first to set up the environment:
    echo   setup_env.bat
    echo.
    echo This will create the virtual environment and install all dependencies.
    pause
    exit /b 1
)

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Failed to activate virtual environment
    echo Try running setup_env.bat to recreate the environment
    pause
    exit /b 1
)

echo ✅ Virtual environment activated

REM Check if .env file exists
if not exist ".env" (
    echo ⚠️  Configuration file .env not found!
    echo Creating basic .env file...
    echo Please edit .env with your Google OAuth credentials
    echo.
    (
        echo # TDMS Configuration - Edit with your credentials
        echo DESKTOP_GOOGLE_OAUTH_CLIENT_ID=your_desktop_client_id_here
        echo DESKTOP_GOOGLE_OAUTH_CLIENT_SECRET=your_desktop_client_secret_here
        echo GOOGLE_OAUTH_CLIENT_ID=your_web_client_id_here
        echo GOOGLE_OAUTH_CLIENT_SECRET=your_web_client_secret_here
        echo GOOGLE_PICKER_APP_ID=your_picker_app_id_here
    ) > .env
)

echo.
echo 🚀 Starting TDMS Desktop Application...
echo    Port: Auto-detected (8001-8099)
echo    Mode: Desktop with embedded web server
echo.

REM Start the application
python -m src.desktop.simple_app

if errorlevel 1 (
    echo.
    echo ========================================
    echo ❌ Failed to start TDMS Desktop Application
    echo ========================================
    echo.
    echo 🔧 Troubleshooting Steps:
    echo.
    echo 1. Run setup_env.bat to reinstall dependencies:
    echo      setup_env.bat
    echo.
    echo 2. Check if Python 3.7+ is installed:
    echo      python --version
    echo.
    echo 3. Verify all project files are present
    echo.
    echo 4. Edit .env file with your Google OAuth credentials
    echo.
    echo 📋 Required dependencies:
    echo    ✓ fastapi[all]     - Web framework
    echo    ✓ pywebview        - Desktop window
    echo    ✓ python-dotenv    - Configuration
    echo    ✓ uvicorn          - Web server
    echo.
    echo 🔑 Required .env variables:
    echo    ✓ DESKTOP_GOOGLE_OAUTH_CLIENT_ID
    echo    ✓ DESKTOP_GOOGLE_OAUTH_CLIENT_SECRET
    echo.
    echo If problems persist, try:
    echo    setup_env.bat
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ Application closed successfully.
pause



