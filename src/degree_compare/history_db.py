from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .config import get_db_path

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS comparisons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url_pair_hash TEXT UNIQUE NOT NULL,
    comparison_json TEXT NOT NULL,
    alert_count INTEGER NOT NULL,
    timestamp TEXT NOT NULL
);
"""


@dataclass
class HistoryRecord:
    url_pair_hash: str
    comparison_json: str
    alert_count: int
    timestamp: str


class HistoryRepository:
    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = Path(db_path) if db_path else get_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(SCHEMA_SQL)
            conn.commit()

    def fetch(self, url_pair_hash: str) -> Optional[HistoryRecord]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT url_pair_hash, comparison_json, alert_count, timestamp FROM comparisons WHERE url_pair_hash = ?",
                (url_pair_hash,),
            ).fetchone()
        if not row:
            return None
        return HistoryRecord(*row)

    def save(self, url_pair_hash: str, comparison_json: str, alert_count: int) -> None:
        timestamp = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO comparisons (url_pair_hash, comparison_json, alert_count, timestamp)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(url_pair_hash) DO UPDATE SET
                    comparison_json = excluded.comparison_json,
                    alert_count = excluded.alert_count,
                    timestamp = excluded.timestamp
                """,
                (url_pair_hash, comparison_json, alert_count, timestamp),
            )
            conn.commit()
