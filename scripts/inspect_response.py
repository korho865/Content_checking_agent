from __future__ import annotations

import sys
from pprint import pprint

from google.genai import types

from degree_compare.config import get_api_key
from degree_compare.gemini_client import GeminiComparisonClient


def dump_response(url_a: str, url_b: str) -> None:
    """Call Gemini with the usual prompt and print raw response details."""
    client = GeminiComparisonClient(api_key=get_api_key())
    contents = [types.Content(role="user", parts=[types.Part(text=client._build_prompt(url_a, url_b))])]
    response = client.client.models.generate_content(
        model=client.model_name,
        contents=contents,
        config=client.generation_config,
    )

    print("response.text repr:", repr(response.text))
    for idx, candidate in enumerate(response.candidates or []):
        print(f"Candidate {idx}: finish_reason={candidate.finish_reason}")
        for part_idx, part in enumerate(candidate.content.parts):
            if hasattr(part, "text") and part.text:
                preview = part.text[:400].replace("\n", " ")
                print(f"  Part {part_idx} text preview: {preview}...")
            else:
                print(f"  Part {part_idx} has type {type(part)}")
    print("\nFull response payload as dict:")
    if hasattr(response, "model_dump"):
        pprint(response.model_dump())
    else:
        pprint(response)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: inspect_response.py <url_a> <url_b>")
    dump_response(sys.argv[1], sys.argv[2])
