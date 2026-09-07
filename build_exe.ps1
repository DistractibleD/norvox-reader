# Builds a standalone TextReader.exe (no Python install required to run it).
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

pyinstaller --noconfirm --clean --onedir --windowed --name TextReader `
    --add-data "vendor;vendor" `
    main.py

Write-Host ""
Write-Host "Build complete: dist\TextReader\TextReader.exe" -ForegroundColor Green
Write-Host "The whole dist\TextReader folder is the app - copy/zip all of it, not just the .exe." -ForegroundColor Yellow
