
from __future__ import annotations

import json
from textwrap import dedent

from google import genai
from google.genai import errors, types

from .config import DEFAULT_MODEL, DEFAULT_TIMEOUT_SECONDS


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
            response_mime_type="application/json",
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
        text_payload = response.text or ";".join(
            part.text for candidate in response.candidates for part in candidate.content.parts if hasattr(part, "text")
        )
        json.loads(text_payload)  # validates well-formed JSON to fail fast
        return text_payload
