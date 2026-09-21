from enum import Enum, auto
from dataclasses import dataclass

class QuestionIntent(Enum):
    TEXT = auto()
    CODE = auto()
    VISUAL = auto()
    MIXED = auto()
    GENERAL = auto()
    UNSUPPORTED = auto()

class ContextRequirement(Enum):
    OCR_ONLY = auto()
    IMAGE_ONLY = auto()
    OCR_AND_IMAGE = auto()
    NONE = auto()

@dataclass
class RouteDecision:
    intent: QuestionIntent
    context_requirement: ContextRequirement
    confidence: float
    reason: str
    selected_backend: str = "Unknown"
