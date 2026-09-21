from dataclasses import dataclass
from typing import Optional

@dataclass
class VisionResult:
    answer: str
    backend: str
    success: bool
    confidence: Optional[float] = None
    inference_time_ms: float = 0.0
    error: Optional[str] = None
    
    @classmethod
    def failure(cls, error_message: str, backend: str = "Unknown") -> "VisionResult":
        return cls(
            answer="",
            backend=backend,
            success=False,
            error=error_message
        )
