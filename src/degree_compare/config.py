from __future__ import annotations


import os
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "history.db"
API_KEY_ENV_VAR = "GOOGLE_API_KEY"
DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_TIMEOUT_SECONDS = 90


def get_db_path() -> Path:
    return Path(os.environ.get("DEGREE_COMPARE_DB", DEFAULT_DB_PATH))


def get_api_key() -> str:
    api_key = os.environ.get(API_KEY_ENV_VAR)
    if not api_key:
        raise RuntimeError(
            f"Missing {API_KEY_ENV_VAR}. Export it before running the comparison."
        )
    return api_key
