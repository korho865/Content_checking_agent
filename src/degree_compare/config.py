from __future__ import annotations


import os
from pathlib import Path

from .secret_store import load_saved_api_key

DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "history.db"
API_KEY_ENV_VAR = "GOOGLE_API_KEY"
DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_TIMEOUT_SECONDS = 180


def get_db_path() -> Path:
    return Path(os.environ.get("DEGREE_COMPARE_DB", DEFAULT_DB_PATH))


def get_api_key() -> str:
    api_key = os.environ.get(API_KEY_ENV_VAR)
    if api_key:
        return api_key
    saved_key = load_saved_api_key()
    if saved_key:
        return saved_key
    raise RuntimeError(
        f"Missing {API_KEY_ENV_VAR}. Export it or save it via the application settings before running the comparison."
    )
