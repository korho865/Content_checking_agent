from __future__ import annotations

import argparse
import hashlib
import sys

from .comparison import ComparisonResult
from .config import get_api_key
from .gemini_client import GeminiComparisonClient
from .history_db import HistoryRepository


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Semantic comparison of two Finnish degree descriptions",
    )
    parser.add_argument("--url-a", required=True, help="First degree description URL")
    parser.add_argument("--url-b", required=True, help="Second degree description URL")
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Ignore cached results and call Gemini regardless",
    )
    return parser


def _hash_pair(url_a: str, url_b: str) -> str:
    normalized = "||".join(sorted([url_a.strip(), url_b.strip()]))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _render(result: ComparisonResult) -> None:
    badge = {
        "green": "[GREEN MATCH]",
        "yellow": "[YELLOW WARNING]",
        "red": "[RED ALERT]",
    }[result.alert_level]
    print(badge, result.alert_message)
    print()
    for field in result.fields:
        prefix = "[MATCH]" if field.status == "MATCH" else "[DIFF ]"
        print(f"{prefix} {field.label}: {field.value_a or 'n/a'}")
        if field.status == "DIFF":
            print(f"       vs {field.value_b or 'n/a'}")
            if field.explanation:
                print(f"       Note: {field.explanation}")
        print()


def cli_entry(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    repo = HistoryRepository()
    url_hash = _hash_pair(args.url_a, args.url_b)
    cached = None if args.force_refresh else repo.fetch(url_hash)

    if cached:
        comparison_json = cached.comparison_json
    else:
        api_key = get_api_key()
        client = GeminiComparisonClient(api_key=api_key)
        comparison_json = client.compare(args.url_a, args.url_b)
        repo.save(url_hash, comparison_json, alert_count=ComparisonResult.from_raw_json(comparison_json).alert_count)

    result = ComparisonResult.from_raw_json(comparison_json)
    _render(result)


if __name__ == "__main__":
    cli_entry(sys.argv[1:])
