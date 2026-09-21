"""
AI Worker — runs AI Orchestrator in a background QThread.
"""
import logging
from typing import Optional
from PySide6.QtCore import QObject, Signal, Slot
from app.ai.orchestrator import AIOrchestrator, AIOrchestratorResult
from app.capture.models import CaptureResult
from app.ai.ocr.models import OCRResult

logger = logging.getLogger(__name__)

class AIWorker(QObject):
    """
    QObject-based worker designed to run in a separate QThread via moveToThread.
    Never directly modifies UI widgets — all results are emitted via signals.
    """
    finished = Signal(AIOrchestratorResult)
    error = Signal(str)

    def __init__(
        self, 
        question: str, 
        capture: Optional[CaptureResult],
        ocr: Optional[OCRResult],
        orchestrator: AIOrchestrator
    ):
        super().__init__()
        self.question = question
        self.capture = capture
        self.ocr = ocr
        self.orchestrator = orchestrator

    @Slot()
    def process(self):
        """Run orchestrated inference. Called from the worker thread."""
        try:
            result = self.orchestrator.ask(self.question, self.capture, self.ocr)
            self.finished.emit(result)
        except Exception as e:
            logger.error(f"AIWorker unexpected error: {e}")
            self.error.emit(str(e))
