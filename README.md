# Content Checking Agent

Python 3.14 prototype that compares two university degree descriptions semantically using Gemini 2.5 with `url_context`. Phase 1 exposes a CLI while Phase 2 adds a Tkinter GUI wrapper.

## Getting Started

1. **Install dependencies** (Python 3.14 environment):
   ```bash
   pip install -e .
   ```
2. **Configure the Gemini API key**:
   ```bash
   set GOOGLE_API_KEY=your-key-here   # Windows PowerShell
   ```
3. **Run the CLI**:
   ```bash
   degree-compare --url-a https://example.com/a --url-b https://example.com/b
   ```
4. **Launch the GUI**:
   ```bash
   degree-compare-gui
   ```

The application caches every comparison in `history.db` so repeated URL pairs reuse the stored response instead of consuming extra tokens.

## Packaging into a Single Executable (Windows)

Build a GUI-only `.exe` with one command:

```powershell
./scripts/build_exe.ps1
```

Output:

- `dist/DegreeCompare.exe`

Notes:

- The app creates `history.db` next to the `.exe` when running as a packaged build.
- API key is requested in the GUI and stored per-user in `%APPDATA%/DegreeCompare/config.json`.

## Building a Windows Installer (Setup EXE)

Prerequisite: install Inno Setup 6 (includes `ISCC.exe`).

Build installer with one command:

```powershell
./scripts/build_installer.ps1
```

Output:

- `installer-output/DegreeCompare-Setup.exe`

The installer places the app in Program Files and optionally creates a desktop shortcut.

## Alert Colors

| Level | Meaning |
| --- | --- |
| Green | All nine critical fields are semantic matches |
| Yellow | Non-critical fields differ |
| Red | Major student-impacting fields (fees, language, scope, curriculum) differ |

## Project Structure

```
src/
  degree_compare/
    __init__.py
    __main__.py
    cli.py
    gui.py
    config.py
    constants.py
    history_db.py
    gemini_client.py
    comparison.py
```
