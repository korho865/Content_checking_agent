# Degree Compare

Degree Compare is a Windows-focused app for comparing Finnish higher-education degree pages with Gemini (`url_context`).

It supports two views:

- Degree comparison: compares key fields like language, scope, fees, study mode, and curriculum.
- Curriculum comparison: compares curriculum content at course/module level and lists outliers only.

## What Users See

- Desktop GUI (Tkinter), no terminal needed.
- API key prompt on first use.
- Previous comparisons list in the app.
- Red `DIFF` highlighting in results.

## Data and Key Storage

- API key file: `%APPDATA%\DegreeCompare\config.json`
- Local history database: `%LOCALAPPDATA%\DegreeCompare\history.db`

No Git push is needed for history updates; data is stored locally on each machine.

## Run From Source (Developers)

Requirements:

- Python 3.14+

Setup:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

Run GUI:

```powershell
.\.venv\Scripts\python.exe -m degree_compare.gui
```

Run CLI:

```powershell
.\.venv\Scripts\python.exe -m degree_compare.cli --url-a https://example.com/a --url-b https://example.com/b
```

## Build Single EXE (Windows)

```powershell
./scripts/build_exe.ps1
```

Output:

- `dist/DegreeCompare.exe`

## Build Windows Installer (Setup EXE)

This produces a normal installer for non-technical users.

```powershell
./scripts/build_installer.ps1
```

Output:

- `installer-output/DegreeCompare-Setup.exe`

Installer behavior:

- Installs app to Program Files.
- Optional desktop shortcut.
- Start Menu entry.
- Standard uninstall support via Windows Apps settings.

## Quick Install Test Checklist

1. Run the latest setup file.
2. Start the app from Start Menu.
3. Enter two URLs and click Compare.
4. Enter a valid Gemini API key when prompted.
5. Verify results render and history updates.
6. Restart app and verify key/history persist.

## Troubleshooting

- `No module named degree_compare`:
   Use the project venv interpreter (`.venv\Scripts\python.exe`) and install with `pip install -e .`.
- `unable to open database file` in installed app:
   Use the latest installer; DB is stored under `%LOCALAPPDATA%\DegreeCompare`.
- Installer build cannot find `ISCC.exe`:
   Install Inno Setup 6 and rerun `./scripts/build_installer.ps1`.

## Project Layout

```text
app_gui.py
installer/
   DegreeCompare.iss
scripts/
   build_exe.ps1
   build_installer.ps1
src/
   degree_compare/
      cli.py
      config.py
      constants.py
      comparison.py
      gemini_client.py
      gui.py
      history_db.py
      secret_store.py
```
