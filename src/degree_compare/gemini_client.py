
from __future__ import annotations

import json
from typing import Any

import google.generativeai as genai

from .config import DEFAULT_MODEL, DEFAULT_TIMEOUT_SECONDS


class GeminiComparisonClient:
    """Thin wrapper around Gemini 2.5 with url_context enabled."""

    def __init__(
        self,
        api_key: str,
        model_name: str = DEFAULT_MODEL,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name=model_name,
            tools=[{"url_context": {}}],
        )
        self.timeout_seconds = timeout_seconds
        self.generation_config = {
            "temperature": 0.1,
            "response_mime_type": "application/json",
        }

    def _build_prompt(self) -> str:
        return t"""You are a semantic comparison assistant for Finnish higher education programs.
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

    def compare(self, url_a: str, url_b: str) -> str:
        prompt = self._build_prompt()
        response = self.model.generate_content(
            [
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt},
                        {"url_context": {"urls": [url_a, url_b]}}
                    ],
                }
            ],
            generation_config=self.generation_config,
            request_options={"timeout": self.timeout_seconds},
        )
        text_payload = response.text or ";".join(
            part.text for candidate in response.candidates for part in candidate.content.parts if hasattr(part, "text")
        )
        json.loads(text_payload)  # validates well-formed JSON to fail fast
        return text_payload
