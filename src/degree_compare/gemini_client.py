
from __future__ import annotations

import json
from textwrap import dedent

from google import genai
from google.genai import types

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
        self.client = genai.Client(api_key=api_key)
        self.timeout_seconds = timeout_seconds
        self.generation_config = types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type="application/json",
            tools=[types.Tool(url_context=types.UrlContext())],
            http_options=types.HttpOptions(timeout=timeout_seconds),
        )

    def _build_prompt(self) -> str:
                return dedent(
                        """You are a semantic comparison assistant for Finnish higher education programs.
Analyze the two degree description URLs given via url_context and output strictly valid JSON.
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

    def compare(self, url_a: str, url_b: str) -> str:
        prompt = self._build_prompt()
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt},
                        {"url_context": {"urls": [url_a, url_b]}},
                    ],
                }
            ],
            config=self.generation_config,
        )
        text_payload = response.text or ";".join(
            part.text for candidate in response.candidates for part in candidate.content.parts if hasattr(part, "text")
        )
        json.loads(text_payload)  # validates well-formed JSON to fail fast
        return text_payload
