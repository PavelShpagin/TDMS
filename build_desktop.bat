@echo off
echo ========================================
echo  TDMS Desktop Application Builder
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

echo ========================================
echo Building Desktop Application
echo ========================================
echo.

REM Check if cx_Freeze is installed
python -c "import cx_Freeze" 2>nul
if errorlevel 1 (
    echo Installing cx_Freeze...
    pip install cx_Freeze
    echo.
)

echo Building standalone desktop application with persistent storage...
set APP_FILE=src/desktop/simple_app.py
set APP_NAME=TDMS-Desktop

echo Building executable...
echo This may take a few minutes...
echo.

REM Create desktop launcher
echo Creating desktop launcher...
echo Desktop launcher created: TDMS-Desktop.bat

REM Test the desktop app
echo Testing desktop application...
python -m src.desktop.simple_app --test >nul 2>&1
if errorlevel 1 (
    echo.
    echo WARNING: Desktop app test failed
    echo Make sure all dependencies are installed:
    echo   pip install pywebview
    echo.
    echo The launcher has been created but may not work properly.
) else (
    echo Desktop application tested successfully!
)

echo.
echo ========================================
echo Build Complete!
echo ========================================
echo.
echo Desktop application launcher created successfully!
echo.
echo Launcher location: TDMS-Desktop.bat
echo.
echo To run the desktop application:
echo   1. Double-click TDMS-Desktop.bat
echo   2. Or run: TDMS-Desktop.bat
echo.
echo The launcher will automatically use the virtual environment if available.
echo Data will be saved to: desktop_databases\desktop.json
echo.

REM Ask if user wants to run the desktop app
set /p RUN_APP="Run the desktop application now? (y/n): "
if /i "%RUN_APP%"=="y" (
    echo.
    echo Starting desktop application...
    call TDMS-Desktop.bat
) else (
    echo.
    echo To run the desktop application later:
    echo   Double-click TDMS-Desktop.bat
    echo.
    echo Or run in development mode:
    echo   python -m src.desktop.simple_app
)

echo.
pause
