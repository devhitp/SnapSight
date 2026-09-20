"""
LLM Worker — runs local LLM inference in a background QThread.
"""
import logging
from PySide6.QtCore import QObject, Signal, Slot
from app.ai.llm.engine import LLMEngine
from app.ai.llm.models import LLMResult

logger = logging.getLogger(__name__)


class LLMWorker(QObject):
    """
    QObject-based worker designed to run in a separate QThread via moveToThread.
    Never directly modifies UI widgets — all results are emitted via signals.
    """
    finished = Signal(LLMResult)
    error = Signal(str)

    def __init__(self, question: str, context: str, engine: LLMEngine):
        super().__init__()
        self.question = question
        self.context = context
        self.engine = engine

    @Slot()
    def generate(self):
        """Run LLM inference. Called from the worker thread."""
        try:
            result = self.engine.generate(self.question, self.context)
            self.finished.emit(result)
        except Exception as e:
            logger.error(f"LLMWorker unexpected error: {e}")
            self.error.emit(str(e))
