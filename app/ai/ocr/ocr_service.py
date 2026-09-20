"""
OCR Service layer.
"""
import time
import logging
from PySide6.QtGui import QImage
from app.capture.models import CaptureResult
from app.ai.ocr.models import OCRResult
from app.ai.ocr.runtime import detect_runtime, RuntimeStatus
from app.ai.ocr.easyocr_engine import EasyOCREngine

logger = logging.getLogger(__name__)

class OCRService:
    def __init__(self):
        self._runtime_status: RuntimeStatus = detect_runtime()
        self._engine = None
        
        if self._runtime_status.available:
            # We strictly instantiate the CPU fallback for this sprint
            self._engine = EasyOCREngine()

    @property
    def is_available(self) -> bool:
        return self._runtime_status.available and self._engine is not None

    def process_capture(self, capture: CaptureResult) -> OCRResult:
        """
        Process a CaptureResult to extract OCR text.
        """
        if not self.is_available:
            raise RuntimeError("OCR service is currently unavailable.")
            
        if not capture.is_valid:
            raise ValueError("Invalid CaptureResult provided for OCR.")
            
        start_time = time.perf_counter()
        
        try:
            regions = self._engine.process_image(capture.image)
        except Exception as e:
            logger.error(f"OCR Engine failed: {e}")
            raise
            
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000.0
        
        runtime_info = f"{self._runtime_status.backend.value} ({self._runtime_status.acceleration.value})"
        
        return OCRResult(
            regions=regions,
            image_width=capture.width,
            image_height=capture.height,
            processing_time_ms=duration_ms,
            engine_name=self._engine.engine_name,
            runtime_info=runtime_info
        )
