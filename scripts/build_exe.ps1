$ErrorActionPreference = "Stop"

Set-Location (Join-Path $PSScriptRoot "..")

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    throw "Virtual environment not found at .venv. Create it first and install dependencies."
}

$python = ".venv\Scripts\python.exe"

& $python -m pip install --upgrade pip
& $python -m pip install pyinstaller

& $python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --noconsole `
    --name DegreeCompare `
    app_gui.py

Write-Host "Build completed: dist\DegreeCompare.exe"
