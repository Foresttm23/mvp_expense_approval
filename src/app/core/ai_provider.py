from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    async def analyse(self, prompt: str) -> str:
        """
        Send *prompt* to the language model and return the raw text response.

        Parameters
        ----------
        prompt:
            The fully-rendered user/system prompt to send.

        Returns
        -------
        str
            Raw text returned by the model (may be JSON, plain text, etc.).

        Raises
        ------
        Exception
            Any network, auth, or model error; callers (``AIService``) are
            expected to handle and degrade gracefully.
        """
