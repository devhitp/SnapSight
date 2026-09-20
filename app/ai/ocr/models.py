"""
OCR Data Models.
"""
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class OCRTextRegion:
    text: str
    confidence: float
    # Bounding box coordinates in pixels relative to the captured image
    x: int
    y: int
    width: int
    height: int

@dataclass
class OCRResult:
    regions: List[OCRTextRegion]
    image_width: int
    image_height: int
    processing_time_ms: float
    engine_name: str
    runtime_info: str
    
    @property
    def full_text(self) -> str:
        """Helper to get all detected text joined by newlines."""
        return "\n".join([r.text for r in self.regions])
