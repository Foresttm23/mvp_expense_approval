from __future__ import annotations

import asyncio
import json

from loguru import logger

from app.core.ai_provider import LLMProvider
from app.core.enums import AIAnalysisStatus
from app.models.expense import Expense
from app.schemas.ai import AIAnalysisResponse

_SYSTEM_PROMPT = """\
You are a financial compliance assistant.
Analyse the expense claim provided and respond **only** with a valid JSON object
matching this exact schema (no markdown fences, no extra keys):

{
  "summary": "<1–2 sentence executive summary of the expense>",
  "is_inconsistent": <true | false>,
  "inconsistency_reason": "<short explanation if is_inconsistent is true, else null>"
}

Rules:
- "summary" must concisely describe the purpose and amount of the expense.
- Set "is_inconsistent" to true if the amount, category, or description are
  mismatched or suspicious (e.g. category is OFFICE but description mentions
  a flight; unusually large amounts for the stated category).
- "inconsistency_reason" must be null when "is_inconsistent" is false.
- Match the language of an expense claim if its in [Ukrainian, Russian, English],
  else respond in English.
"""


def _build_prompt(expense: Expense) -> str:
    return (
        f"{_SYSTEM_PROMPT}\n\n"
        f"Expense details:\n"
        f"- Category   : {expense.category}\n"
        f"- Amount     : ${expense.amount}\n"
        f"- Date       : {expense.expense_date}\n"
        f"- Description: {expense.description}\n"
    )


class AIService:
    def __init__(self, provider: LLMProvider, timeout: float = 3.0) -> None:
        self._provider = provider
        self._timeout = timeout

    async def analyse_expense(self, expense: Expense) -> AIAnalysisResponse:
        """
        Analyze an expense claim and return an advisory response.

        This method is non-blocking, any failure causes fallback response.

        Returns
        -------
        AIAnalysisResponse
            Populated on success; fallback payload on any failure.
        """
        log = logger.bind(expense_id=str(expense.id))

        prompt = _build_prompt(expense)

        try:
            async with asyncio.timeout(self._timeout):
                raw: str = await self._provider.analyse(prompt)
        except TimeoutError:
            log.warning(
                f"AI provider timed out after {self._timeout}s — returning fallback"
            )
            return AIAnalysisResponse.fallback(AIAnalysisStatus.UNAVAILABLE)
        except Exception as exc:
            log.warning(f"AI provider raised an error — returning fallback: {exc}")
            return AIAnalysisResponse.fallback(AIAnalysisStatus.ERROR)

        try:
            data: dict = json.loads(raw)
            return AIAnalysisResponse(
                summary=data.get("summary"),
                is_inconsistent=bool(data.get("is_inconsistent", False)),
                inconsistency_reason=data.get("inconsistency_reason"),
                status=AIAnalysisStatus.AVAILABLE,
            )
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            log.warning(
                f"AI provider returned unparseable response — returning fallback: {exc}"
            )
            return AIAnalysisResponse.fallback(AIAnalysisStatus.ERROR)
