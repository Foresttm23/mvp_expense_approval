from typing import Self

from app.core.enums import AIAnalysisStatus
from app.schemas.base import OutputModel


class AIAnalysisResponse(OutputModel):
    summary: str | None = None
    is_inconsistent: bool = False
    inconsistency_reason: str | None = None
    status: AIAnalysisStatus = AIAnalysisStatus.AVAILABLE

    @classmethod
    def fallback(cls, status: AIAnalysisStatus = AIAnalysisStatus.UNAVAILABLE) -> Self:
        return cls(
            summary=None,
            is_inconsistent=False,
            inconsistency_reason=None,
            status=status,
        )
