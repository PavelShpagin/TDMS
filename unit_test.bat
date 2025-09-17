@echo off
echo ========================================
echo  TDMS Unit Test Suite
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

REM Install additional test dependencies
echo Installing test dependencies...
pip install pytest-cov pytest-html --quiet

echo ========================================
echo Running Unit Tests
echo ========================================
echo.

REM Run tests with different options based on user choice
echo Select test mode:
echo 1. Quick test (no coverage)
echo 2. Full test with coverage
echo 3. Desktop app tests only
echo 4. Core module tests only
echo 5. Web API tests only
echo.

set /p CHOICE="Enter your choice (1-5): "

if "%CHOICE%"=="1" (
    echo Running quick tests...
    python -m pytest tests/ -v --tb=short
) else if "%CHOICE%"=="2" (
    echo Running full tests with coverage...
    python -m pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html:htmlcov --tb=short
) else if "%CHOICE%"=="3" (
    echo Running desktop app tests...
    python -m pytest tests/test_desktop_api.py -v --tb=short
) else if "%CHOICE%"=="4" (
    echo Running core module tests...
    python -m pytest tests/test_core.py -v --tb=short
) else if "%CHOICE%"=="5" (
    echo Running web API tests...
    python -m pytest tests/test_web_api.py -v --tb=short
) else (
    echo Invalid choice. Running all tests with coverage...
    python -m pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html:htmlcov --tb=short
)

if errorlevel 1 (
    echo.
    echo SOME TESTS FAILED!
    set TEST_RESULT=FAILED
) else (
    echo.
    echo ALL TESTS PASSED!
    set TEST_RESULT=PASSED
)

echo.
echo ========================================
echo Test Summary
echo ========================================
echo.
echo Test Result: %TEST_RESULT%
echo.

REM Show coverage report if it exists
if exist "htmlcov\index.html" (
    echo Coverage report generated: htmlcov\index.html
    set /p OPEN_REPORT="Open coverage report in browser? (y/n): "
    if /i "%OPEN_REPORT%"=="y" (
        start htmlcov\index.html
    )
)

echo.
echo Test run completed.
pause



