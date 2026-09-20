"""
LLM Result Data Model.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMResult:
    """Structured result from a local LLM generation call."""
    answer: str
    model_name: str
    runtime_info: str
    generation_time_ms: float
    success: bool
    # Optional — only populated if the runtime actually exposes these
    prompt_tokens: Optional[int] = None
    generated_tokens: Optional[int] = None
    error: Optional[str] = None

    @property
    def tokens_per_sec(self) -> Optional[float]:
        """Returns tokens/sec only when both counters and timing are available."""
        if self.generated_tokens and self.generation_time_ms > 0:
            return (self.generated_tokens / self.generation_time_ms) * 1000.0
        return None

    @classmethod
    def failure(cls, error: str, model_name: str = "unknown", runtime_info: str = "unknown") -> "LLMResult":
        return cls(
            answer="",
            model_name=model_name,
            runtime_info=runtime_info,
            generation_time_ms=0.0,
            success=False,
            error=error,
        )
