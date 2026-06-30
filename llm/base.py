"""Common interface and errors for text-generation providers."""

from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProviderError(RuntimeError):
    """Raised when a configured LLM cannot generate a response."""


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate a text response for a complete prompt."""
        raise NotImplementedError
