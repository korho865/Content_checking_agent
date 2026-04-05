$ErrorActionPreference = "Stop"

Set-Location (Join-Path $PSScriptRoot "..")

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    throw "Virtual environment not found at .venv. Create it first and install dependencies."
}

# Ensure the latest single-file app exists.
& powershell -ExecutionPolicy Bypass -File .\scripts\build_exe.ps1

$iscc = $null
$cmd = Get-Command iscc -ErrorAction SilentlyContinue
if ($cmd) {
    $iscc = $cmd.Source
}

if (-not $iscc) {
    $candidatePaths = @(
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe",
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
    )
    foreach ($candidate in $candidatePaths) {
        if (Test-Path $candidate) {
            $iscc = $candidate
            break
        }
    }
}

if (-not $iscc) {
    $searchRoots = @("C:\Program Files", "C:\Program Files (x86)", "$env:LOCALAPPDATA\Programs")
    foreach ($root in $searchRoots) {
        if (-not (Test-Path $root)) {
            continue
        }
        $match = Get-ChildItem -Path $root -Filter ISCC.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($match) {
            $iscc = $match.FullName
            break
        }
    }
}

if (-not $iscc) {
    throw "Inno Setup compiler (ISCC.exe) not found. Install Inno Setup 6 from https://jrsoftware.org/isinfo.php and rerun this script."
}

& $iscc .\installer\DegreeCompare.iss

Write-Host "Installer completed: installer-output\DegreeCompare-Setup.exe"
