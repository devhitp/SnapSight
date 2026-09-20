"""
Data models for the screen capture pipeline.
"""
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, Any, Optional
from PySide6.QtGui import QImage

class CaptureType(Enum):
    FULLSCREEN = auto()
    WINDOW = auto()
    REGION = auto()
    UNKNOWN = auto()

class CaptureState(Enum):
    NONE = auto()
    CAPTURING = auto()
    SUCCESS = auto()
    FAILED = auto()
    CANCELLED = auto()

@dataclass
class CaptureResult:
    """
    Model representing a completed capture.
    The canonical image format is QImage to keep the backend decoupled from UI renderers (QPixmap).
    """
    image: QImage
    width: int
    height: int
    capture_type: CaptureType
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_valid(self) -> bool:
        return not self.image.isNull() and self.width > 0 and self.height > 0
