# Builds Norvox Reader for distribution: a self-contained app folder, then
# packages it TWO ways so users on differently-restricted PCs can pick:
#   1. A single-file installer (installer_output\NorvoxReaderSetup-X.Y.Z.exe)
#      - needs Inno Setup (installed automatically below if missing)
#      - deliberately needs NO admin rights (installs to the user's own
#        AppData folder, never triggers UAC) - see installer.iss
#   2. A portable .zip (dist\NorvoxReader-vX.Y.Z-portable.zip)
#      - just extract anywhere and run "Norvox Reader.exe" inside
#      - no installer logic at all, so it works even on machines where
#        running any installer/script is restricted
#
# Usage: right-click > Run with PowerShell, or run from a terminal:
#   powershell -ExecutionPolicy Bypass -File build_exe.ps1

$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

. .\.venv\Scripts\Activate.ps1

pip install --upgrade pip | Out-Null
pip install -r requirements.txt
pip install pyinstaller

pyinstaller --noconfirm --clean --onedir --windowed --name "Norvox Reader" `
    --add-data "vendor;vendor" `
    main.py

$version = (& .\.venv\Scripts\python.exe -c "from app.version import __version__; print(__version__)").Trim()
Write-Host ""
Write-Host "Built dist\Norvox Reader\ (version $version)" -ForegroundColor Green

# --- 1. Portable .zip -------------------------------------------------------

$zipPath = "dist\NorvoxReader-v$version-portable.zip"
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
Compress-Archive -Path "dist\Norvox Reader" -DestinationPath $zipPath
Write-Host "Portable zip: $zipPath" -ForegroundColor Green

# --- 2. Single-file installer (Inno Setup) ---------------------------------

$isccCmd = Get-Command ISCC.exe -ErrorAction SilentlyContinue
if ($isccCmd) {
    $isccPath = $isccCmd.Path
} else {
    $candidates = @(
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
    )
    $isccPath = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
}

if (-not $isccPath) {
    Write-Host "Inno Setup not found - installing via winget..." -ForegroundColor Yellow
    winget install --id JRSoftware.InnoSetup -e --silent --accept-package-agreements --accept-source-agreements
    $isccPath = "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
}

& $isccPath "/DMyAppVersion=$version" "installer.iss"
Write-Host "Installer: installer_output\NorvoxReaderSetup-$version.exe" -ForegroundColor Green

Write-Host ""
Write-Host "Done. Two ways to distribute this build:" -ForegroundColor Cyan
Write-Host "  - installer_output\NorvoxReaderSetup-$version.exe  (no admin needed, but is a proper installer)"
Write-Host "  - dist\NorvoxReader-v$version-portable.zip          (just extract and run, no installer at all)"
