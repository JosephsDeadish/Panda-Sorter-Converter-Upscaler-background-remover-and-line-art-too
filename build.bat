@echo off
REM ============================================================================
REM Game Texture Sorter - Automated Windows Build Script
REM Author: Dead On The Inside / JosephsDeadish
REM 
REM This script automatically builds the single-EXE application for Windows.
REM It will:
REM   1. Check for Python installation
REM   2. Create/activate virtual environment
REM   3. Install dependencies
REM   4. Run PyInstaller to create EXE
REM   5. Package the final executable
REM ============================================================================

echo.
echo ========================================================================
echo   Game Texture Sorter - Automated Build Script
echo   Author: Dead On The Inside / JosephsDeadish
echo ========================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or later from https://www.python.org/
    pause
    exit /b 1
)

echo [1/6] Python found: 
python --version
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo [2/6] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully.
) else (
    echo [2/6] Virtual environment already exists.
)
echo.

REM Activate virtual environment
echo [3/6] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo.

REM Upgrade pip
echo [4/6] Upgrading pip...
python -m pip install --upgrade pip
echo.

REM Install dependencies
echo [5/6] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo Dependencies installed successfully.
echo.

REM Clean previous builds
echo [6/6] Cleaning previous builds...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "*.spec" del /q *.spec
echo.

REM Create necessary resource directories if they don't exist
if not exist "src\resources\icons" mkdir src\resources\icons
if not exist "src\resources\cursors" mkdir src\resources\cursors
if not exist "src\resources\themes" mkdir src\resources\themes
if not exist "src\resources\sounds" mkdir src\resources\sounds

REM Create a placeholder icon if it doesn't exist
if not exist "src\resources\icons\panda_icon.ico" (
    echo Creating placeholder icon...
    REM PyInstaller will use default icon if custom one doesn't exist
)

echo ========================================================================
echo   Building Single EXE with PyInstaller...
echo ========================================================================
echo.

REM Run PyInstaller with spec file
pyinstaller build_spec.spec --clean --noconfirm
if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    echo Check the error messages above for details.
    pause
    exit /b 1
)

echo.
echo ========================================================================
echo   BUILD SUCCESSFUL!
echo ========================================================================
echo.
echo The executable has been created in the 'dist' folder:
echo   dist\GameTextureSorter.exe
echo.
echo File size:
dir dist\GameTextureSorter.exe | find "GameTextureSorter.exe"
echo.
echo You can now:
echo   1. Run the EXE directly: dist\GameTextureSorter.exe
echo   2. Copy it to any location (it's portable)
echo   3. Sign it with a code certificate (see CODE_SIGNING.md)
echo   4. Distribute it to users
echo.
echo The EXE is completely standalone and requires no installation!
echo ========================================================================
echo.

pause
