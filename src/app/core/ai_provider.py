from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    async def analyse(self, prompt: str) -> str:
        """
        Send *prompt* to the language model and return the raw text response.
        """
