"""
OCR Engine abstraction.
"""
from abc import ABC, abstractmethod
from typing import List, Tuple
from PySide6.QtGui import QImage
from app.ai.ocr.models import OCRTextRegion

class OCREngine(ABC):
    """
    Abstract base class for OCR engines.
    Isolates external dependencies (like easyocr or onnxruntime) from the rest of the application.
    """
    
    @abstractmethod
    def process_image(self, image: QImage) -> List[OCRTextRegion]:
        """
        Processes a QImage and returns a list of detected text regions.
        """
        pass
        
    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Returns the name of the engine."""
        pass
