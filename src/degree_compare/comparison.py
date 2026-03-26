from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Literal

from .constants import CRITICAL_FIELDS, FIELD_SPECS

StatusLiteral = Literal["MATCH", "DIFF", "UNKNOWN"]


@dataclass
class FieldComparison:
    key: str
    label: str
    status: StatusLiteral
    value_a: str | None = None
    value_b: str | None = None
    explanation: str | None = None


@dataclass
class ComparisonResult:
    url_a: str
    url_b: str
    fields: list[FieldComparison] = field(default_factory=list)

    @property
    def alert_count(self) -> int:
        return sum(1 for field in self.fields if field.status == "DIFF")

    @property
    def alert_level(self) -> str:
        if self.alert_count == 0:
            return "green"
        if any(field.key in CRITICAL_FIELDS and field.status == "DIFF" for field in self.fields):
            return "red"
        return "yellow"

    @property
    def alert_message(self) -> str:
        match self.alert_level:
            case "green":
                return "All monitored fields match semantically."
            case "yellow":
                return "Minor differences detected in non-critical fields."
            case "red":
                return "Critical fields differ; review before advising students."
            case _:
                return "Comparison incomplete."

    def to_json(self) -> str:
        payload = {
            "url_a": self.url_a,
            "url_b": self.url_b,
            "fields": [field.__dict__ for field in self.fields],
            "alert_level": self.alert_level,
            "alert_message": self.alert_message,
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)

    @staticmethod
    def from_raw_json(raw_text: str) -> "ComparisonResult":
        data = json.loads(raw_text)
        field_lookup = {spec.key: spec for spec in FIELD_SPECS}
        parsed_fields: list[FieldComparison] = []
        for entry in data.get("fields", []):
            key = entry.get("field") or entry.get("key")
            spec = field_lookup.get(key, None)
            label = spec.label if spec else key or "Tuntematon"
            parsed_fields.append(
                FieldComparison(
                    key=key or "unknown",
                    label=label,
                    status=(entry.get("status") or "UNKNOWN").upper(),
                    value_a=entry.get("value_a"),
                    value_b=entry.get("value_b"),
                    explanation=entry.get("explanation"),
                )
            )
        return ComparisonResult(
            url_a=data.get("url_a", ""),
            url_b=data.get("url_b", ""),
            fields=parsed_fields,
        )
