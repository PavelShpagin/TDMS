@echo off
echo ========================================
echo  TDMS Web Server
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and add it to your PATH
    pause
    exit /b 1
)

echo Python version:
python --version
echo.

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
    echo Virtual environment activated.
    echo.
) else (
    echo No virtual environment found. Using system Python.
    echo To create a virtual environment, run setup_environment.bat
    echo.
)

REM Install dependencies if needed
echo Checking dependencies...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo WARNING: Some dependencies may not be installed correctly
    echo.
)

echo Starting TDMS Web Server...
echo.
echo Server will be available at:
echo   http://localhost:8000
echo   http://127.0.0.1:8000
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

REM Start the FastAPI server with uvicorn
python -m uvicorn src.web.main:app --port 8000 --reload

echo.
echo Server stopped.
pause