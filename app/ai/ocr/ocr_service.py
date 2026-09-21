"""
OCR Service layer.
"""
import time
import logging
from PySide6.QtGui import QImage
from app.capture.models import CaptureResult
from app.ai.ocr.models import OCRResult
from app.ai.ocr.runtime import detect_runtime, RuntimeStatus, AccelerationType
from app.ai.ocr.easyocr_engine import EasyOCREngine
from app.ai.ocr.qualcomm_engine import QualcommOCREngine

logger = logging.getLogger(__name__)

class OCRService:
    def __init__(self):
        self._runtime_status: RuntimeStatus = detect_runtime()
        self._engine = None
        
        self._initialize_engine()

    def _initialize_engine(self):
        """
        OCRRuntimeSelector logic.
        Attempts Qualcomm if discoverable, otherwise falls back to EasyOCR.
        """
        if self._runtime_status.backend == "qualcomm":
            try:
                self._engine = QualcommOCREngine()
                self._runtime_status.execution.available = True
                self._runtime_status.execution.accelerator = AccelerationType.NPU
                self._runtime_status.execution.reason = "Qualcomm NPU execution verified."
                logger.info("Qualcomm OCR backend initialized successfully.")
                return
            except Exception as e:
                logger.warning(f"Qualcomm backend initialization failed: {e}. Falling back to CPU.")
                # Fallback to EasyOCR
                self._runtime_status.backend = "easyocr"
                self._runtime_status.execution.accelerator = AccelerationType.CPU
                self._runtime_status.execution.reason = f"Fallback to CPU due to Qualcomm error: {e}"

        if self._runtime_status.backend == "easyocr":
            try:
                self._engine = EasyOCREngine()
                self._runtime_status.execution.available = True
                self._runtime_status.execution.accelerator = AccelerationType.CPU
                logger.info("EasyOCR CPU backend initialized successfully.")
            except Exception as e:
                logger.error(f"EasyOCR backend initialization failed: {e}")
                self._runtime_status.execution.available = False
                self._runtime_status.execution.reason = f"EasyOCR init failed: {e}"

    @property
    def is_available(self) -> bool:
        return self._runtime_status.execution.available and self._engine is not None

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
        
        runtime_info = f"{self._engine.engine_name} ({self._runtime_status.execution.accelerator.value})"
        
        return OCRResult(
            regions=regions,
            image_width=capture.width,
            image_height=capture.height,
            processing_time_ms=duration_ms,
            engine_name=self._engine.engine_name,
            runtime_info=runtime_info
        )
