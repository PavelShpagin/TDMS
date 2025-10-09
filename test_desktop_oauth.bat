@echo off
echo ====================================
echo TDMS Desktop OAuth Test
echo ====================================
echo.
echo This will:
echo 1. Start the desktop app
echo 2. Wait for you to test OAuth
echo 3. Instructions will appear
echo.
echo Press Ctrl+C to exit when done testing
echo.
pause

echo.
echo Starting desktop app...
echo.
python -m src.desktop.simple_app

echo.
echo Desktop app closed.
pause


