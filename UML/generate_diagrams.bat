@echo off
REM TDMS UML Diagram Generator Script for Windows
REM This script generates PNG images from PlantUML files

echo =========================================
echo TDMS UML Diagram Generator
echo =========================================

REM Check if Java is installed
java -version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Java is not installed. Please install Java first.
    echo Download from: https://www.java.com/download/
    pause
    exit /b 1
)

REM Download PlantUML if not present
if not exist "plantuml.jar" (
    echo Downloading PlantUML...
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/plantuml/plantuml/releases/download/v1.2024.0/plantuml-1.2024.0.jar' -OutFile 'plantuml.jar'"
    if %errorlevel% neq 0 (
        echo Error: Failed to download PlantUML
        echo Please download manually from: https://plantuml.com/download
        pause
        exit /b 1
    )
    echo PlantUML downloaded successfully!
)

REM Create output directory for PNGs
if not exist "images" mkdir images

REM Generate PNG for each PlantUML file
echo.
echo Generating PNG diagrams...
echo -----------------------------------------

for %%f in (*.puml) do (
    echo Processing: %%f
    java -jar plantuml.jar -tpng "%%f" -o images/
    if %errorlevel% equ 0 (
        echo   √ Generated: images\%%~nf.png
    ) else (
        echo   × Failed to generate PNG for %%f
    )
)

echo -----------------------------------------
echo.

REM Count and display generated files
echo Generated files:
dir /b images\*.png 2>nul
if %errorlevel% neq 0 (
    echo No PNG files were generated.
) else (
    echo.
    echo Successfully generated PNG diagrams!
)

echo.
echo =========================================
echo Generation complete!
echo =========================================
pause