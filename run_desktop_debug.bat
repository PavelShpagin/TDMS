@echo off
echo [TDMS Desktop Debug Mode]
echo.

REM Kill any existing Python processes
taskkill /F /IM python.exe >nul 2>&1
timeout /t 1 /nobreak >nul

REM Check for .env
if not exist .env (
    echo [!] No .env found, creating basic one...
    echo REDIS_URL=redis://localhost:6379/0 > .env
    echo GOOGLE_CLIENT_ID=your_client_id >> .env
    echo GOOGLE_CLIENT_SECRET=your_client_secret >> .env
    echo.
)

echo [+] Starting desktop app with debug output...
echo [+] Watch for any errors below:
echo.
echo ========================================
uv run python -m src.desktop.simple_app
echo ========================================
echo.
echo [X] Desktop app closed
pause


