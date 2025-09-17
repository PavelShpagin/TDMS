@echo off
echo ========================================
echo  TDMS Environment Setup
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and add it to your PATH
    echo You can download Python from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python version:
python --version
echo.

REM Remove existing virtual environment if corrupted
if exist "venv" (
    echo Removing existing virtual environment...
    rmdir /s /q venv
    echo.
)

REM Create fresh virtual environment
echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)
echo Virtual environment created successfully.
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    echo Trying alternative activation method...
    venv\Scripts\python.exe -m pip --version >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Virtual environment is not working properly
        pause
        exit /b 1
    )
    echo Using virtual environment Python directly...
    set PYTHON_CMD=venv\Scripts\python.exe
    set PIP_CMD=venv\Scripts\pip.exe
    goto :skip_activation
)
set PYTHON_CMD=python
set PIP_CMD=pip

:skip_activation

echo Virtual environment activated.
echo.

REM Upgrade pip
echo Upgrading pip...
%PYTHON_CMD% -m pip install --upgrade pip
echo.

REM Install dependencies
echo Installing dependencies from requirements.txt...
%PIP_CMD% install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install some dependencies
    echo Please check the error messages above
    pause
    exit /b 1
)

echo.
echo Installing additional development dependencies...
%PIP_CMD% install pytest-cov pytest-html black flake8 mypy requests
echo.

echo ========================================
echo Environment Setup Complete!
echo ========================================
echo.
echo Your TDMS environment is now ready to use.
echo.
echo Available commands:
echo   run_server.bat     - Start the web server
echo   build_desktop.bat  - Build and run the desktop application
echo   unit_test.bat      - Run all tests with coverage
echo.
echo To manually activate the virtual environment:
echo   venv\Scripts\activate.bat
echo.
echo To deactivate the virtual environment:
echo   deactivate
echo.

pause
