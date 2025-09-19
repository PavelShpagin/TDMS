@echo off
echo ========================================
echo  TDMS UML Diagram Generator (Windows)
echo ========================================
echo.

REM Check if mermaid-cli is installed
mmdc --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Mermaid CLI not found!
    echo Please install with: npm install -g @mermaid-js/mermaid-cli
    pause
    exit /b 1
)

echo Mermaid CLI found.
echo.

REM Create images directory if it doesn't exist
if not exist "images" mkdir images

REM Count .mmd files
set count=0
for %%f in (*.mmd) do set /a count+=1

echo Found %count% Mermaid files to process
echo Output directory: images\
echo.

REM Export all .mmd files to PNG with better quality
set success=0
for %%f in (*.mmd) do (
    echo Processing %%f...
    mmdc -i "%%f" -o "images\%%~nf.png" -t neutral -b white --width 1200 --height 800
    if not errorlevel 1 (
        echo   ✓ Generated: images\%%~nf.png
        set /a success+=1
    ) else (
        echo   ✗ Failed: %%f
    )
)

echo.
echo ========================================
echo Results: %success%/%count% diagrams generated
echo ========================================

if %success%==%count% (
    echo All diagrams generated successfully!
) else (
    echo Some diagrams failed to generate.
)

echo.
echo Generated files:
dir images\*.png /b

pause