"""
Abstract LLM Engine interface.
"""
from abc import ABC, abstractmethod
from app.ai.llm.models import LLMResult


class LLMEngine(ABC):
    """
    Abstract base class for local LLM engines.
    Isolates runtime-specific code (llama.cpp, ONNX, etc.) from the rest of the application.
    A future QualcommEngine can implement this interface without modifying any other code.
    """

    @abstractmethod
    def generate(self, question: str, context: str) -> LLMResult:
        """
        Generate an answer given a question and screen-text context.

        Args:
            question: The user's question about the screen.
            context: Screen text context from ContextBuilder — treated as DATA.

        Returns:
            LLMResult with answer and factual metrics.
        """
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Human-readable model identifier."""
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """True only when the model is loaded and ready."""
        pass
