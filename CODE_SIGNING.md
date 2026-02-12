# Code Signing Guide for Game Texture Sorter

This guide explains how to digitally sign your Game Texture Sorter EXE to avoid Windows SmartScreen warnings and establish trust with users.

## Why Code Signing?

Without code signing, Windows will show:
- **"Windows protected your PC"** SmartScreen warning
- **"Unknown publisher"** in file properties
- **Trust prompts** when users try to run your app

With code signing:
- ✓ No SmartScreen warnings (after reputation builds)
- ✓ Your name/company shown as verified publisher
- ✓ Users can verify the file hasn't been tampered with
- ✓ Professional appearance and trust

## What You Need

### 1. Code Signing Certificate

You need an **Authenticode Code Signing Certificate**. Options:

**Commercial Certificate Authorities** (Recommended):
- **DigiCert** - $319-474/year
  - Most trusted CA
  - Fast validation
  - Good reputation
- **Sectigo (formerly Comodo)** - $179-299/year
  - Affordable option
  - Well-recognized
- **GlobalSign** - $299-399/year
- **SSL.com** - $159-299/year

**Individual vs Organization Certificates**:
- **Individual (OV)**: Requires identity verification (~$200-300/year)
- **Organization (OV)**: Requires business verification (~$300-500/year)
- **EV Code Signing**: Highest trust, requires hardware token (~$300-600/year)

**Note**: EV (Extended Validation) certificates provide immediate SmartScreen reputation and are recommended for commercial software.

### 2. Signing Tools

**Windows SDK (Included with Visual Studio)**:
- Download: [Windows SDK](https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/)
- Provides `signtool.exe`
- Free

**Or use SignTool from Windows 10/11**:
- Already included in `C:\Program Files (x86)\Windows Kits\10\bin\<version>\x64\signtool.exe`

## Step-by-Step Signing Process

### Step 1: Obtain Certificate

1. Purchase certificate from a CA
2. Complete identity/organization verification (can take 1-5 business days)
3. Download certificate and private key
4. Install in Windows Certificate Store

**Installing Certificate**:
```cmd
# Import PFX/P12 certificate
certutil -user -p PASSWORD -importpfx certificate.pfx
```

Or double-click the `.pfx` file and follow the wizard.

### Step 2: Locate SignTool

Find `signtool.exe` on your system:

```powershell
# Search for signtool
Get-ChildItem -Path "C:\Program Files (x86)\Windows Kits" -Recurse -Filter signtool.exe | Select-Object FullName
```

Typical locations:
- `C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe`
- `C:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x64\signtool.exe`

Add to PATH or use full path when signing.

### Step 3: Sign the EXE

#### Option A: Sign with Installed Certificate
```cmd
signtool sign /a /tr http://timestamp.digicert.com /td SHA256 /fd SHA256 "dist\GameTextureSorter.exe"
```

**Parameters explained**:
- `/a` - Automatically select best certificate
- `/tr` - Timestamp server URL (RFC 3161)
- `/td SHA256` - Timestamp digest algorithm
- `/fd SHA256` - File digest algorithm

#### Option B: Sign with PFX File
```cmd
signtool sign /f "certificate.pfx" /p PASSWORD /tr http://timestamp.digicert.com /td SHA256 /fd SHA256 "dist\GameTextureSorter.exe"
```

**Parameters**:
- `/f` - Certificate file path
- `/p` - Certificate password

#### Option C: Sign with Hardware Token (EV Certificate)
```cmd
signtool sign /n "Your Company Name" /tr http://timestamp.digicert.com /td SHA256 /fd SHA256 "dist\GameTextureSorter.exe"
```

**Parameters**:
- `/n` - Certificate subject name

### Step 4: Verify Signature

```cmd
signtool verify /pa /v "dist\GameTextureSorter.exe"
```

**Expected output**:
```
Verifying: dist\GameTextureSorter.exe
Hash of file (sha256): XXXXX...
Signing Certificate Chain:
...
Successfully verified: dist\GameTextureSorter.exe
```

## Timestamp Servers

Always use a timestamp server! This allows your signature to remain valid even after your certificate expires.

**Recommended Timestamp Servers**:
- DigiCert: `http://timestamp.digicert.com`
- GlobalSign: `http://timestamp.globalsign.com/scripts/timstamp.dll`
- Sectigo: `http://timestamp.sectigo.com`
- SSL.com: `http://ts.ssl.com`

## Automated Signing Script

Create `sign.bat` for easy signing:

```batch
@echo off
REM Automated Code Signing Script
REM Update paths and certificate details for your environment

SET SIGNTOOL="C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe"
SET EXE_PATH="dist\GameTextureSorter.exe"
SET CERT_NAME="Your Company Name"
SET TIMESTAMP="http://timestamp.digicert.com"

echo Signing %EXE_PATH%...
%SIGNTOOL% sign /n %CERT_NAME% /tr %TIMESTAMP% /td SHA256 /fd SHA256 %EXE_PATH%

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Successfully signed!
    echo.
    echo Verifying signature...
    %SIGNTOOL% verify /pa /v %EXE_PATH%
) else (
    echo.
    echo ERROR: Signing failed!
    exit /b 1
)

pause
```

## PowerShell Signing Script

Create `sign.ps1`:

```powershell
# Code Signing Script for Game Texture Sorter
# Author: Dead On The Inside / JosephsDeadish

$SignTool = "C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe"
$ExePath = "dist\GameTextureSorter.exe"
$CertName = "Your Company Name"  # Update this
$Timestamp = "http://timestamp.digicert.com"

Write-Host "Signing $ExePath..." -ForegroundColor Yellow

& $SignTool sign /n $CertName /tr $Timestamp /td SHA256 /fd SHA256 $ExePath

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Successfully signed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Verifying signature..." -ForegroundColor Yellow
    & $SignTool verify /pa /v $ExePath
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Signature verified!" -ForegroundColor Green
    }
} else {
    Write-Host "✗ ERROR: Signing failed!" -ForegroundColor Red
    exit 1
}

Read-Host "Press Enter to continue"
```

## Checking Signed EXE Properties

After signing, verify:

1. **Right-click EXE** → **Properties**
2. Go to **Digital Signatures** tab
3. You should see your certificate
4. Double-click signature → **Details** → View certificate
5. Check:
   - Valid timestamp
   - Valid signature
   - Publisher name correct
   - Certificate not expired

## Windows SmartScreen Reputation

Even with a valid signature, new certificates may still trigger SmartScreen warnings initially. To build reputation:

1. **Get an EV certificate** - Immediate reputation
2. **Submit to Microsoft** - [SmartScreen file reputation](https://www.microsoft.com/en-us/wdsi/filesubmission)
3. **Distribute normally** - Reputation builds as users download and run
4. **Time** - Usually takes 2-4 weeks for OV certificates

## Troubleshooting

### "Certificate not found"
- Make sure certificate is installed: `certmgr.msc`
- Check certificate name: `signtool sign /a` (auto-select)

### "SignTool not found"
- Install Windows SDK
- Add to PATH or use full path

### "Timestamp server error"
- Try different timestamp server
- Check internet connection
- Retry signing (network timeout)

### "Certificate expired"
- Purchase new certificate
- Timestamp ensures old signatures remain valid

### SmartScreen still showing warnings
- EV certificate recommended for immediate trust
- Submit file to Microsoft
- Wait for reputation to build

## Best Practices

1. **Always timestamp** - Signatures remain valid after cert expires
2. **Use SHA256** - SHA1 is deprecated
3. **Backup certificates** - Store PFX files securely
4. **Automate signing** - Include in build pipeline
5. **Verify after signing** - Always check signature is valid
6. **Version control** - Don't commit certificates to git!
7. **Secure storage** - Use hardware tokens for private keys (EV certs)

## Build + Sign Pipeline

Combined build and sign script:

```batch
@echo off
echo Building and signing Game Texture Sorter...
echo.

REM Build
call build.bat
if errorlevel 1 exit /b 1

REM Sign
call sign.bat
if errorlevel 1 exit /b 1

echo.
echo ========================================
echo Build and sign completed successfully!
echo ========================================
```

## Cost Summary

**One-time costs**:
- Windows SDK: Free
- Build tools: Free

**Recurring costs**:
- Code signing certificate: $159-$600/year
  - OV (Organization): $179-$299/year (SmartScreen reputation builds over time)
  - EV (Extended Validation): $300-$600/year (Immediate SmartScreen reputation)

**Recommendation for this project**:
- **Personal/Free**: No signing, users see SmartScreen warning
- **Indie Developer**: OV certificate ($179-$299) - Professional appearance
- **Commercial**: EV certificate ($300-$600) - Best user experience

## Alternative: Self-Signed Certificates

For testing only (NOT for distribution):

```cmd
# Create self-signed certificate
New-SelfSignedCertificate -DnsName "GameTextureSorter" -Type CodeSigning -CertStoreLocation Cert:\CurrentUser\My

# Export and sign
# Note: Users will still see warnings unless they install your certificate
```

**Not recommended for distribution** - Users will see bigger warnings than unsigned!

## Resources

- [Microsoft: SignTool Documentation](https://docs.microsoft.com/en-us/windows/win32/seccrypto/signtool)
- [Code Signing Best Practices](https://docs.microsoft.com/en-us/windows-hardware/drivers/dashboard/code-signing-best-practices)
- [SmartScreen Reputation](https://docs.microsoft.com/en-us/windows/security/threat-protection/intelligence/smartscreen-reputation)

---

**Author**: Dead On The Inside / JosephsDeadish
