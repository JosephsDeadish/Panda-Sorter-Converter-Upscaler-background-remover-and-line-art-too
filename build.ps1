#!/usr/bin/env pwsh
################################################################################
# Game Texture Sorter - Automated Windows Build Script (PowerShell)
# Author: Dead On The Inside / JosephsDeadish
#
# This PowerShell script automatically builds the single-EXE application.
# It provides better error handling and progress reporting than the batch file.
################################################################################

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "  Game Texture Sorter - Automated Build Script (PowerShell)" -ForegroundColor Cyan
Write-Host "  Author: Dead On The Inside / JosephsDeadish" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

# Check Python installation
Write-Host "[1/6] Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8 or later from https://www.python.org/" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host ""

# Create virtual environment
Write-Host "[2/6] Setting up virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Gray
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ ERROR: Failed to create virtual environment" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "✓ Virtual environment already exists" -ForegroundColor Green
}
Write-Host ""

# Activate virtual environment
Write-Host "[3/6] Activating virtual environment..." -ForegroundColor Yellow
$activateScript = "venv\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
    Write-Host "✓ Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "✗ ERROR: Activation script not found" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host ""

# Upgrade pip
Write-Host "[4/6] Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet
Write-Host "✓ pip upgraded" -ForegroundColor Green
Write-Host ""

# Install dependencies
Write-Host "[5/6] Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ ERROR: Failed to install dependencies" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "✓ Dependencies installed" -ForegroundColor Green
Write-Host ""

# Clean previous builds
Write-Host "[6/6] Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
    Write-Host "✓ Removed build directory" -ForegroundColor Gray
}
if (Test-Path "dist") {
    Remove-Item -Recurse -Force "dist"
    Write-Host "✓ Removed dist directory" -ForegroundColor Gray
}
Get-ChildItem -Path . -Filter "*.spec" -Exclude "build_spec.spec" | Remove-Item -Force
Write-Host "✓ Cleaned previous builds" -ForegroundColor Green
Write-Host ""

# Create resource directories
Write-Host "Creating resource directories..." -ForegroundColor Yellow
$resourceDirs = @(
    "src\resources\icons",
    "src\resources\cursors",
    "src\resources\themes",
    "src\resources\sounds"
)
foreach ($dir in $resourceDirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "✓ Created $dir" -ForegroundColor Gray
    }
}
Write-Host ""

# Build with PyInstaller
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "  Building Single EXE with PyInstaller..." -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

pyinstaller build_spec.spec --clean --noconfirm

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "✗ BUILD FAILED!" -ForegroundColor Red
    Write-Host "Check the error messages above for details." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "========================================================================" -ForegroundColor Green
Write-Host "  ✓ BUILD SUCCESSFUL!" -ForegroundColor Green
Write-Host "========================================================================" -ForegroundColor Green
Write-Host ""

# Check if EXE was created
$exePath = "dist\GameTextureSorter.exe"
if (Test-Path $exePath) {
    $exeSize = (Get-Item $exePath).Length
    $exeSizeMB = [math]::Round($exeSize / 1MB, 2)
    
    Write-Host "The executable has been created:" -ForegroundColor White
    Write-Host "  Location: $exePath" -ForegroundColor Cyan
    Write-Host "  Size: $exeSizeMB MB" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "You can now:" -ForegroundColor White
    Write-Host "  1. Run the EXE: .\$exePath" -ForegroundColor Gray
    Write-Host "  2. Copy it anywhere (fully portable)" -ForegroundColor Gray
    Write-Host "  3. Sign it with a code certificate (see CODE_SIGNING.md)" -ForegroundColor Gray
    Write-Host "  4. Distribute to users" -ForegroundColor Gray
    Write-Host ""
    Write-Host "The EXE is completely standalone - no installation required! 🐼" -ForegroundColor Green
} else {
    Write-Host "✗ WARNING: EXE file not found at expected location" -ForegroundColor Yellow
}

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

Read-Host "Press Enter to exit"
