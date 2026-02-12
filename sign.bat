@echo off
REM ============================================================================
REM Game Texture Sorter - Code Signing Script
REM Author: Dead On The Inside / JosephsDeadish
REM
REM This script signs the built EXE with a code signing certificate.
REM Update the variables below with your certificate details.
REM ============================================================================

echo.
echo ========================================================================
echo   Game Texture Sorter - Code Signing
echo   Author: Dead On The Inside / JosephsDeadish
echo ========================================================================
echo.

REM ============================================================================
REM CONFIGURATION - Update these variables for your environment
REM ============================================================================

REM Path to signtool.exe (update based on your Windows SDK version)
SET SIGNTOOL="C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe"

REM Path to the EXE to sign
SET EXE_PATH="dist\GameTextureSorter.exe"

REM Certificate details (choose ONE method below)
REM Method 1: Use installed certificate (by subject name)
SET CERT_NAME="Your Company Name Here"

REM Method 2: Use PFX file (uncomment and set password if using this method)
REM SET CERT_FILE="path\to\certificate.pfx"
REM SET CERT_PASSWORD="YourPasswordHere"

REM Timestamp server (recommended: DigiCert)
SET TIMESTAMP="http://timestamp.digicert.com"

REM ============================================================================

REM Check if EXE exists
if not exist %EXE_PATH% (
    echo ERROR: EXE file not found: %EXE_PATH%
    echo Please build the application first using build.bat
    pause
    exit /b 1
)

REM Check if signtool exists
if not exist %SIGNTOOL% (
    echo ERROR: SignTool not found at: %SIGNTOOL%
    echo.
    echo Please update SIGNTOOL path in this script or install Windows SDK
    echo Download from: https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/
    pause
    exit /b 1
)

echo Signing %EXE_PATH%...
echo.

REM Sign using installed certificate (default method)
%SIGNTOOL% sign /n %CERT_NAME% /tr %TIMESTAMP% /td SHA256 /fd SHA256 %EXE_PATH%

REM Uncomment below and comment above to use PFX file instead:
REM %SIGNTOOL% sign /f %CERT_FILE% /p %CERT_PASSWORD% /tr %TIMESTAMP% /td SHA256 /fd SHA256 %EXE_PATH%

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================================
    echo   Signing Successful!
    echo ========================================================================
    echo.
    echo Verifying signature...
    echo.
    %SIGNTOOL% verify /pa /v %EXE_PATH%
    
    if %ERRORLEVEL% EQU 0 (
        echo.
        echo ========================================================================
        echo   Signature Verified!
        echo ========================================================================
        echo.
        echo The EXE is now signed and ready for distribution.
        echo Users will see your verified publisher name.
        echo.
    ) else (
        echo.
        echo WARNING: Verification failed. Check signature details.
        echo.
    )
) else (
    echo.
    echo ========================================================================
    echo   ERROR: Signing Failed!
    echo ========================================================================
    echo.
    echo Please check:
    echo   1. Certificate is installed correctly
    echo   2. Certificate name matches: %CERT_NAME%
    echo   3. Certificate is not expired
    echo   4. You have internet connection (for timestamping)
    echo.
    echo Run 'certmgr.msc' to view installed certificates
    echo.
    echo For more help, see CODE_SIGNING.md
    echo.
    pause
    exit /b 1
)

pause
