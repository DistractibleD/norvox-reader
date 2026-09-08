<#
Norvox Reader - source-based installer for PCs that block the normal
.exe/installer downloads (school/work PCs with strict SmartScreen or
AppLocker-style policies that leave no "Run anyway" option).

Installs Python via winget if needed, downloads the app's source code
and bundled Tesseract OCR files from the latest GitHub release, sets up
a private virtual environment, creates a Desktop shortcut, and launches
the app - no unsigned .exe from us is ever executed.

Usage (run in PowerShell):
    powershell -ExecutionPolicy Bypass -File install-from-source.ps1

Or, without downloading the file first:
    irm https://raw.githubusercontent.com/DistractibleD/norvox-reader/main/install-from-source.ps1 | iex
#>

$ErrorActionPreference = "Stop"
$RepoOwner = "DistractibleD"
$RepoName = "norvox-reader"
$InstallDir = "$env:LOCALAPPDATA\NorvoxReaderSource"

function Write-Step($msg) {
    Write-Host ""
    Write-Host "==> $msg" -ForegroundColor Cyan
}

Write-Step "Checking for Python..."
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Step "Python not found - installing via winget (no admin rights needed)..."
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $winget) {
        Write-Host "winget is not available on this PC." -ForegroundColor Red
        Write-Host "Please install Python manually from https://python.org (check 'Add python.exe to PATH'), then run this script again."
        exit 1
    }
    winget install --id Python.Python.3.12 -e --source winget --scope user --silent --accept-package-agreements --accept-source-agreements
    Write-Host ""
    Write-Host "Python was just installed. Please close this window and run this script again" -ForegroundColor Yellow
    Write-Host "so it can pick up the new Python installation." -ForegroundColor Yellow
    exit 0
}

Write-Step "Finding the latest Norvox Reader release..."
$release = Invoke-RestMethod -UseBasicParsing "https://api.github.com/repos/$RepoOwner/$RepoName/releases/latest"
$tag = $release.tag_name
Write-Host "Latest version: $tag"

$tesseractAsset = $release.assets | Where-Object { $_.name -eq "vendor_tesseract.zip" }
if (-not $tesseractAsset) {
    Write-Host "Could not find the bundled Tesseract OCR download in the latest release." -ForegroundColor Red
    Write-Host "Screen-capture OCR won't work, but the rest of the app can still be installed."
}

if (Test-Path $InstallDir) {
    Write-Step "Removing previous install at $InstallDir..."
    Remove-Item $InstallDir -Recurse -Force
}
New-Item -ItemType Directory -Path $InstallDir | Out-Null

Write-Step "Downloading app source ($tag)..."
$sourceZip = "$env:TEMP\norvox-source.zip"
Invoke-WebRequest -UseBasicParsing -Uri "https://github.com/$RepoOwner/$RepoName/archive/refs/tags/$tag.zip" -OutFile $sourceZip
Expand-Archive -Path $sourceZip -DestinationPath "$env:TEMP\norvox-source-extracted" -Force
$extractedFolder = Get-ChildItem "$env:TEMP\norvox-source-extracted" -Directory | Select-Object -First 1
Copy-Item "$($extractedFolder.FullName)\*" -Destination $InstallDir -Recurse -Force
Remove-Item $sourceZip -Force
Remove-Item "$env:TEMP\norvox-source-extracted" -Recurse -Force

if ($tesseractAsset) {
    Write-Step "Downloading bundled Tesseract OCR (~60 MB)..."
    $tessZip = "$env:TEMP\norvox-tesseract.zip"
    Invoke-WebRequest -UseBasicParsing -Uri $tesseractAsset.browser_download_url -OutFile $tessZip
    $vendorDir = "$InstallDir\vendor"
    if (Test-Path "$vendorDir\tesseract") { Remove-Item "$vendorDir\tesseract" -Recurse -Force }
    Expand-Archive -Path $tessZip -DestinationPath $vendorDir -Force
    Remove-Item $tessZip -Force
}

Write-Step "Setting up a private Python environment..."
& python -m venv "$InstallDir\venv"
& "$InstallDir\venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
& "$InstallDir\venv\Scripts\pip.exe" install --quiet -r "$InstallDir\requirements.txt"

Write-Step "Creating a Desktop shortcut..."
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut("$env:USERPROFILE\Desktop\Norvox Reader.lnk")
$shortcut.TargetPath = "$InstallDir\venv\Scripts\pythonw.exe"
$shortcut.Arguments = "main.py"
$shortcut.WorkingDirectory = $InstallDir
$shortcut.Description = "Norvox Reader"
$shortcut.Save()

Write-Step "Done! Launching Norvox Reader now..."
Start-Process -FilePath "$InstallDir\venv\Scripts\pythonw.exe" -ArgumentList "main.py" -WorkingDirectory $InstallDir
Write-Host ""
Write-Host "A 'Norvox Reader' shortcut has been added to your Desktop for next time." -ForegroundColor Green
