from abc import ABC, abstractmethod
from PySide6.QtGui import QImage
from .models import VisionResult

class VisionEngine(ABC):
    """
    Abstract interface for multimodal vision engines.
    """
    
    @abstractmethod
    def analyze_image(self, image: QImage, question: str) -> VisionResult:
        """
        Analyze the given image and answer the user's question.
        
        Args:
            image: The captured QImage.
            question: The user's question.
            
        Returns:
            VisionResult containing the answer and metrics.
        """
        pass
        
    @property
    @abstractmethod
    def is_available(self) -> bool:
        pass
        
    @property
    @abstractmethod
    def engine_name(self) -> str:
        pass
