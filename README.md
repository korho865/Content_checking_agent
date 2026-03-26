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

## Packaging into a Single Executable

Use PyInstaller once the prototype is validated:

```bash
pyinstaller --name DegreeCompare --onefile --console src/degree_compare/__main__.py
```

Ship the resulting binary plus the `history.db` seed file (created automatically on first launch).

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
