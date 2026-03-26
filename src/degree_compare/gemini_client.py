
from __future__ import annotations

import json
import re
from textwrap import dedent
from typing import Any

from google import genai
from google.genai import errors, types

from .config import DEFAULT_MODEL, DEFAULT_TIMEOUT_SECONDS


CODE_BLOCK_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)


class GeminiComparisonClient:
    """Thin wrapper around Gemini 2.5 with url_context enabled."""

    def __init__(
        self,
        api_key: str,
        model_name: str = DEFAULT_MODEL,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        timeout_ms = int(timeout_seconds * 1000)
        # Use the same HttpOptions on both the high-level client and the request config
        # so long-running url_context fetches have enough time to complete.
        http_options = types.HttpOptions(timeout=timeout_ms)
        self.client = genai.Client(api_key=api_key, http_options=http_options)
        self.generation_config = types.GenerateContentConfig(
            temperature=0.1,
            tools=[types.Tool(url_context=types.UrlContext())],
            http_options=http_options,
        )

    def _build_prompt(self, url_a: str, url_b: str) -> str:
        instructions = dedent(
            """You are a semantic comparison assistant for Finnish higher education programs.
Analyze the two degree description URLs using the url_context tool and output strictly valid JSON.
Use the schema:
{
  "url_a": string,
  "url_b": string,
  "fields": [
    {
      "field": one of ["opetustapa", "opetusaika", "maksullisuus", "koulutustyyppi", "suunnitelmankesto", "opetuskieli", "koulutuksen_laajuus", "opetussuunnitelma"],
      "status": "MATCH" | "DIFF",
      "value_a": string,
      "value_b": string,
      "explanation": short string if status is "DIFF"
    }
  ]
}
Status must be "MATCH" when two values mean the same thing even if wording differs.
"""
        ).strip()
        url_block = dedent(
            f"""URLs to fetch via url_context:
- url_a: {url_a}
- url_b: {url_b}
"""
        ).strip()
        return f"{instructions}\n\n{url_block}"

    def compare(self, url_a: str, url_b: str) -> str:
        prompt = self._build_prompt(url_a, url_b)
        contents = [types.Content(role="user", parts=[types.Part(text=prompt)])]
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=self.generation_config,
            )
        except errors.ClientError as exc:
            if exc.code == 403 and exc.message and "reported as leaked" in exc.message:
                raise RuntimeError(
                    "Gemini rejected the configured GOOGLE_API_KEY because it has been reported as leaked. "
                    "Generate a fresh key at https://aistudio.google.com/app/apikey, set GOOGLE_API_KEY, and rerun."
                ) from exc
            raise
        parsed_payload = self._extract_json_payload(response)
        return json.dumps(parsed_payload, ensure_ascii=False, indent=2)

    def _extract_json_payload(self, response: types.GenerateContentResponse) -> Any:
        text_candidates: list[str] = []
        if response.text:
            text_candidates.append(response.text)
        for candidate in response.candidates or []:
            for part in candidate.content.parts:
                text = getattr(part, "text", None)
                if text:
                    text_candidates.append(text)

        decoder = json.JSONDecoder()
        for text in text_candidates:
            parsed = self._parse_json_from_text(text, decoder)
            if parsed is not None:
                return parsed

        snippet = text_candidates[0] if text_candidates else ""
        preview = snippet.strip().replace("\n", " ")[:500]
        raise RuntimeError(
            "Gemini responded without a JSON payload that matched the expected schema. "
            f"Sample response text: {preview or '<empty>'}"
        )

    def _parse_json_from_text(self, text: str, decoder: json.JSONDecoder) -> Any | None:
        for candidate in self._candidate_strings(text):
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue

        for match in re.finditer(r"[{[]", text):
            start = match.start()
            try:
                parsed, _ = decoder.raw_decode(text, start)
            except json.JSONDecodeError:
                continue
            return parsed
        return None

    def _candidate_strings(self, text: str) -> list[str]:
        candidates: list[str] = []
        stripped = text.strip()
        if stripped:
            candidates.append(stripped)
        for match in CODE_BLOCK_RE.finditer(text):
            block = match.group(1).strip()
            if block:
                candidates.append(block)
        return candidates
