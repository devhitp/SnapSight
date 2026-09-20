"""
OCR Worker for background processing.
"""
from PySide6.QtCore import QObject, Signal, Slot, QThread
from app.capture.models import CaptureResult
from app.ai.ocr.models import OCRResult
from app.ai.ocr.ocr_service import OCRService
import logging

logger = logging.getLogger(__name__)

class OCRWorker(QObject):
    """
    QObject-based worker designed to run in a separate QThread.
    """
    finished = Signal(OCRResult)
    error = Signal(str)

    def __init__(self, capture_result: CaptureResult, service: OCRService):
        super().__init__()
        self.capture_result = capture_result
        self.service = service

    @Slot()
    def process(self):
        try:
            result = self.service.process_capture(self.capture_result)
            self.finished.emit(result)
        except Exception as e:
            logger.error(f"OCR Worker error: {e}")
            self.error.emit(str(e))
