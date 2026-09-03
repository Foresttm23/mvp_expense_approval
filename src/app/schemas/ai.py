from typing import Self

from app.core.enums import AIAnalysisStatus
from app.schemas.base import OutputModel


class AIAnalysisResponse(OutputModel):
    summary: str | None = None
    is_inconsistent: bool = False
    inconsistency_reason: str | None = None
    status: str = AIAnalysisStatus.AVAILABLE.value

    @classmethod
    def fallback(cls, status: str = AIAnalysisStatus.UNAVAILABLE.value) -> Self:
        """Returns a non-blocking fallback response when AI service fails or times out."""
        return cls(
            summary=None,
            is_inconsistent=False,
            inconsistency_reason=None,
            status=status,
        )
