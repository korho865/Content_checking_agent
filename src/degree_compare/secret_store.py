from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

APP_DIR_NAME = "DegreeCompare"
CONFIG_FILENAME = "config.json"


def _config_dir() -> Path:
    if os.name == "nt":
        base = os.environ.get("APPDATA")
        if base:
            return Path(base) / APP_DIR_NAME
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / APP_DIR_NAME
    return Path.home() / f".{APP_DIR_NAME.lower()}"


def _config_path() -> Path:
    return _config_dir() / CONFIG_FILENAME


def load_saved_api_key() -> str | None:
    path = _config_path()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    api_key = data.get("api_key") if isinstance(data, dict) else None
    if api_key and api_key.strip():
        return api_key.strip()
    return None


def save_api_key(api_key: str) -> None:
    api_key = api_key.strip()
    if not api_key:
        raise ValueError("api_key must be non-empty")
    path = _config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, Any] = {"api_key": api_key}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def clear_saved_api_key() -> None:
    path = _config_path()
    try:
        path.unlink()
    except FileNotFoundError:
        pass
