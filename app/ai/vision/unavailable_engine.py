import time
from PySide6.QtGui import QImage
from .engine import VisionEngine
from .models import VisionResult

class UnavailableVisionEngine(VisionEngine):
    """
    Fallback engine used when no local vision backend is available.
    Safely handles visual routing without crashing the application.
    """
    
    def analyze_image(self, image: QImage, question: str) -> VisionResult:
        start_time = time.time()
        
        # Simulate slight delay so UI doesn't flicker instantly
        time.sleep(0.5)
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        return VisionResult(
            answer="I detected that this is a visual question, but my local vision backend is currently unavailable on this device. I cannot analyze the image contents.",
            backend="Unavailable",
            success=True,
            confidence=1.0,
            inference_time_ms=elapsed_ms
        )
        
    @property
    def is_available(self) -> bool:
        return False
        
    @property
    def engine_name(self) -> str:
        return "UnavailableVisionEngine"
