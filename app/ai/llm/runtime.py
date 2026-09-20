"""
LLM Runtime detection.
"""
import importlib.util
from dataclasses import dataclass
from enum import Enum


class LLMBackend(Enum):
    LLAMA_CPP = "llama.cpp"
    UNKNOWN = "Unknown"


class LLMAcceleration(Enum):
    CPU = "CPU"
    NPU = "NPU"
    UNKNOWN = "Unknown"


@dataclass
class LLMRuntimeStatus:
    backend: LLMBackend
    acceleration: LLMAcceleration
    available: bool
    detail: str = ""


def detect_llm_runtime() -> LLMRuntimeStatus:
    """
    Safely detects whether llama-cpp-python is installed.
    Does NOT claim Qualcomm/NPU acceleration — that requires actual verified
    execution through a Qualcomm backend, which is not implemented in Sprint 4.
    """
    has_llama_cpp = importlib.util.find_spec("llama_cpp") is not None

    if not has_llama_cpp:
        return LLMRuntimeStatus(
            backend=LLMBackend.UNKNOWN,
            acceleration=LLMAcceleration.UNKNOWN,
            available=False,
            detail="llama-cpp-python is not installed. Run: pip install -r requirements-llm.txt",
        )

    return LLMRuntimeStatus(
        backend=LLMBackend.LLAMA_CPP,
        acceleration=LLMAcceleration.CPU,
        available=True,
        detail="llama-cpp-python available (CPU execution)",
    )
