from __future__ import annotations

from google import genai
from google.genai import types as genai_types
from loguru import logger

from app.core.ai_provider import LLMProvider


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str | None, model_name: str) -> None:
        self._model_name = model_name
        if api_key:
            self._client = genai.Client(api_key=api_key)
        else:
            logger.warning(
                "GeminiProvider: GEMINI_API_KEY is not set — "
                "all analyse() calls will raise and trigger the fallback path."
            )
            self._client = None

    async def analyse(self, prompt: str) -> str:
        """
        Send *prompt* to Gemini and return the raw response text.

        Raises:
            RuntimeError: If no API key was provided at construction time.
            google.genai.errors.APIError: On any Gemini API-level failure (network, quota, etc.).
        """
        if self._client is None:
            raise RuntimeError(
                "Gemini client is not initialised — GEMINI_API_KEY is missing."
            )

        response = await self._client.aio.models.generate_content(
            model=self._model_name,
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        return response.text
