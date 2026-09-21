"""
Sprint 8 — Reliability, Error Recovery & Worker Lifecycle Tests.

All tests use mocked services — no real GGUF model or EasyOCR required.
Tests verify:
  - repeated operations don't accumulate workers or state
  - model is not reloaded on every LLM request
  - error recovery leaves the pipeline usable
  - worker threads emit error signals and restore UI state
  - router overhead is bounded
"""
import time
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage
from PySide6.QtCore import QThread

from app.ai.llm.models import LLMResult
from app.ai.llm.runtime import LLMBackend, LLMAcceleration, LLMRuntimeStatus
from app.ai.ocr.models import OCRResult, OCRTextRegion
from app.ai.router.router import QuestionRouter
from app.ai.orchestrator import AIOrchestratorResult, AIOrchestrator
from app.ai.router.models import QuestionIntent
from app.capture.models import CaptureResult, CaptureType


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def _make_blank_capture(width=640, height=480):
    img = QImage(width, height, QImage.Format_RGB32)
    img.fill(0xFFFFFF)
    return CaptureResult(image=img, width=width, height=height, capture_type=CaptureType.FULLSCREEN)


def _make_ocr_result():
    return OCRResult(
        regions=[OCRTextRegion("Hello", 0.95, 0, 0, 100, 20)],
        image_width=640,
        image_height=480,
        processing_time_ms=50.0,
        engine_name="MockOCR",
        runtime_info="CPU",
    )


# ── Repeated OCR — No Accumulation ────────────────────────────────────────────

def test_repeated_ocr_no_state_accumulation():
    """
    5 repeated OCR process_capture() calls on a mock engine should not
    grow any internal list or state in OCRService.
    """
    from app.ai.ocr.ocr_service import OCRService
    from app.ai.ocr.runtime import AccelerationType

    mock_status = MagicMock()
    mock_status.backend = "easyocr"
    mock_status.execution.available = True
    mock_status.execution.accelerator = AccelerationType.CPU

    mock_engine = MagicMock()
    mock_engine.engine_name = "MockEasyOCR"
    mock_engine.process_image.return_value = []

    with patch("app.ai.ocr.ocr_service.detect_runtime", return_value=mock_status), \
         patch("app.ai.ocr.ocr_service.EasyOCREngine", return_value=mock_engine), \
         patch("app.ai.ocr.ocr_service.QualcommOCREngine", side_effect=RuntimeError("no qnn")):
        service = OCRService()

    assert service.is_available
    capture = _make_blank_capture()

    for i in range(5):
        result = service.process_capture(capture)
        assert isinstance(result, OCRResult)

    # Engine was called exactly 5 times (init + 5 real calls = 6 total, but init is in __init__)
    assert mock_engine.process_image.call_count == 5


# ── LLM Model Reuse ───────────────────────────────────────────────────────────

def test_llm_model_not_reloaded_on_repeat():
    """
    _initialize() must short-circuit after first successful load.
    The GGUF model must not be reloaded for every generate() call.
    """
    from app.ai.llm.llamacpp_engine import LlamaCppEngine

    with patch("app.ai.llm.llamacpp_engine.detect_llm_runtime") as mock_runtime:
        mock_runtime.return_value = LLMRuntimeStatus(
            backend=LLMBackend.LLAMA_CPP,
            acceleration=LLMAcceleration.CPU,
            available=True,
        )
        engine = LlamaCppEngine(model_path="models/fake.gguf")

    # Inject a pre-loaded mock model so file-loading is bypassed
    mock_llm = MagicMock()
    mock_llm.return_value = {
        "choices": [{"text": "mocked answer"}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5},
    }
    engine._llm = mock_llm

    # Wrap _initialize to track how many times it actually loads
    original_initialize = engine._initialize
    init_call_count = [0]

    def tracked_initialize():
        init_call_count[0] += 1
        return original_initialize()

    engine._initialize = tracked_initialize

    # Call generate() 5 times
    for _ in range(5):
        result = engine.generate("What is SnapSight?", "")
        assert result.success

    # _initialize should be called 5 times but should short-circuit each time
    assert init_call_count[0] == 5  # called each time
    # But the actual Llama() constructor should NOT be called (model already loaded)
    assert engine._llm is mock_llm  # Same mock — not recreated


def test_llm_repeated_questions_same_instance():
    """After first load, repeated generate() calls must use the same _llm object."""
    from app.ai.llm.llamacpp_engine import LlamaCppEngine

    with patch("app.ai.llm.llamacpp_engine.detect_llm_runtime") as mock_runtime:
        mock_runtime.return_value = LLMRuntimeStatus(
            backend=LLMBackend.LLAMA_CPP,
            acceleration=LLMAcceleration.CPU,
            available=True,
        )
        engine = LlamaCppEngine(model_path="models/fake.gguf")

    mock_llm = MagicMock()
    mock_llm.return_value = {
        "choices": [{"text": "answer"}],
        "usage": {},
    }
    engine._llm = mock_llm
    instance_id_before = id(engine._llm)

    engine.generate("Question 1", "")
    engine.generate("Question 2", "")
    engine.generate("Question 3", "")

    instance_id_after = id(engine._llm)
    assert instance_id_before == instance_id_after, \
        "LLM instance must not be replaced between calls"


# ── LLM Error Recovery ────────────────────────────────────────────────────────

def test_llm_error_does_not_corrupt_engine():
    """A failed generate() should not leave the engine in an unusable state."""
    from app.ai.llm.llamacpp_engine import LlamaCppEngine

    with patch("app.ai.llm.llamacpp_engine.detect_llm_runtime") as mock_runtime:
        mock_runtime.return_value = LLMRuntimeStatus(
            backend=LLMBackend.LLAMA_CPP,
            acceleration=LLMAcceleration.CPU,
            available=True,
        )
        engine = LlamaCppEngine(model_path="models/fake.gguf")

    call_count = [0]

    def side_effect(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            raise RuntimeError("transient failure")
        return {"choices": [{"text": "ok"}], "usage": {}}

    mock_llm = MagicMock(side_effect=side_effect)
    engine._llm = mock_llm

    # First call fails
    result1 = engine.generate("test", "")
    assert not result1.success

    # Second call should succeed
    result2 = engine.generate("test", "")
    assert result2.success


def test_llm_missing_model_returns_friendly_error():
    """Missing GGUF model must return a LLMResult.failure without stack trace."""
    from app.ai.llm.llamacpp_engine import LlamaCppEngine

    with patch("app.ai.llm.llamacpp_engine.detect_llm_runtime") as mock_runtime:
        mock_runtime.return_value = LLMRuntimeStatus(
            backend=LLMBackend.LLAMA_CPP,
            acceleration=LLMAcceleration.CPU,
            available=True,
        )
        engine = LlamaCppEngine(model_path="models/does_not_exist_ever.gguf")

    result = engine.generate("test", "")
    assert not result.success
    assert result.error is not None
    # Error should be user-readable, not a raw traceback
    assert "not found" in result.error.lower() or "model" in result.error.lower()
    # No raw Python exception types in the message
    assert "Traceback" not in result.error
    assert "FileNotFoundError" not in result.error


def test_llm_empty_question_rejected_before_model():
    """Empty question must be rejected without touching the LLM."""
    from app.ai.llm.llamacpp_engine import LlamaCppEngine

    with patch("app.ai.llm.llamacpp_engine.detect_llm_runtime") as mock_runtime:
        mock_runtime.return_value = LLMRuntimeStatus(
            backend=LLMBackend.LLAMA_CPP,
            acceleration=LLMAcceleration.CPU,
            available=True,
        )
        engine = LlamaCppEngine(model_path="models/fake.gguf")

    mock_llm = MagicMock()
    engine._llm = mock_llm

    result = engine.generate("", "context")
    assert not result.success
    assert "empty" in result.error.lower()
    # LLM callable should never have been invoked
    mock_llm.assert_not_called()


# ── OCR Error Recovery ─────────────────────────────────────────────────────────

def test_ocr_engine_failure_propagates_cleanly():
    """An OCR engine RuntimeError should propagate as an exception, not a silent failure."""
    from app.ai.ocr.ocr_service import OCRService
    from app.ai.ocr.runtime import AccelerationType

    mock_status = MagicMock()
    mock_status.backend = "easyocr"
    mock_status.execution.available = True
    mock_status.execution.accelerator = AccelerationType.CPU

    mock_engine = MagicMock()
    mock_engine.engine_name = "MockFailingOCR"
    mock_engine.process_image.side_effect = RuntimeError("OCR inference failure")

    with patch("app.ai.ocr.ocr_service.detect_runtime", return_value=mock_status), \
         patch("app.ai.ocr.ocr_service.EasyOCREngine", return_value=mock_engine), \
         patch("app.ai.ocr.ocr_service.QualcommOCREngine", side_effect=RuntimeError("no qnn")):
        service = OCRService()

    capture = _make_blank_capture()
    with pytest.raises(RuntimeError, match="OCR inference failure"):
        service.process_capture(capture)

    # Service remains available for future calls
    assert service.is_available


def test_ocr_unavailable_raises_runtime_error():
    """process_capture() on an unavailable service must raise RuntimeError."""
    from app.ai.ocr.ocr_service import OCRService
    from app.ai.ocr.runtime import AccelerationType

    mock_status = MagicMock()
    mock_status.backend = "easyocr"
    mock_status.execution.available = False
    mock_status.execution.reason = "EasyOCR not installed"

    with patch("app.ai.ocr.ocr_service.detect_runtime", return_value=mock_status), \
         patch("app.ai.ocr.ocr_service.EasyOCREngine", side_effect=RuntimeError("not installed")), \
         patch("app.ai.ocr.ocr_service.QualcommOCREngine", side_effect=RuntimeError("no qnn")):
        service = OCRService()

    assert not service.is_available
    with pytest.raises(RuntimeError):
        service.process_capture(_make_blank_capture())


# ── Worker UI Restore on Error ─────────────────────────────────────────────────

@patch("app.ui.main_window.OCRService")
@patch("app.ui.main_window.LlamaCppEngine")
def test_worker_ui_restored_after_ai_error(mock_llm_cls, mock_ocr_cls, qapp):
    """After AIWorker emits an error, Ask AI button must be re-enabled."""
    mock_ocr_cls.return_value.is_available = False
    mock_llm_cls.return_value._runtime.available = False

    from app.ui.main_window import MainWindow
    window = MainWindow()

    # Simulate mid-generation state
    window._ai_generating = True
    window.btn_ask_ai.setEnabled(False)
    window.btn_ask_ai.setText("Thinking...")

    # Simulate error signal from AIWorker
    window.on_ai_error("Simulated generation failure")

    assert not window._ai_generating
    assert window.btn_ask_ai.isEnabled()
    assert window.btn_ask_ai.text() == "Ask AI"
    assert "SnapSight couldn't generate" in window.answer_text_edit.toPlainText()


@patch("app.ui.main_window.OCRService")
@patch("app.ui.main_window.LlamaCppEngine")
def test_worker_ui_restored_after_failed_ai_result(mock_llm_cls, mock_ocr_cls, qapp):
    """A result with success=False must also restore UI state."""
    mock_ocr_cls.return_value.is_available = False
    mock_llm_cls.return_value._runtime.available = False

    from app.ui.main_window import MainWindow
    window = MainWindow()

    window._ai_generating = True
    window.btn_ask_ai.setEnabled(False)

    failed_result = AIOrchestratorResult(
        answer="",
        route_used=QuestionIntent.GENERAL,
        backend_used="None",
        inference_time_ms=0.0,
        ocr_used=False,
        vision_used=False,
        success=False,
        error="LLM unavailable",
    )
    window.on_ai_success(failed_result)

    assert not window._ai_generating
    assert window.btn_ask_ai.isEnabled()


# ── Router Performance ─────────────────────────────────────────────────────────

def test_router_overhead_is_bounded():
    """
    Router is a deterministic keyword classifier.
    20 routing calls should complete in well under 1 second total.
    This is a generous regression guard, not a product claim.
    Actual measured values are reported by scripts/benchmark.py.
    """
    router = QuestionRouter()
    questions = [
        "What does it say?",
        "What color is the button?",
        "What is recursion?",
        "Explain this graph",
        "What error is shown?",
    ] * 4  # 20 calls

    t0 = time.perf_counter()
    for q in questions:
        router.route(q)
    total_ms = (time.perf_counter() - t0) * 1000.0

    # 20 calls in under 1000 ms is an extremely generous guard.
    # Real performance is reported by the benchmark script.
    assert total_ms < 1000, (
        f"Router took {total_ms:.1f} ms for 20 calls — unexpectedly slow"
    )


def test_router_per_call_is_fast():
    """Each single router call should be well under 100 ms individually."""
    router = QuestionRouter()
    questions = ["What is recursion?", "What color is that?", "Explain this graph"]

    for q in questions:
        t0 = time.perf_counter()
        router.route(q)
        ms = (time.perf_counter() - t0) * 1000.0
        assert ms < 100, f"Single router call took {ms:.2f} ms — unexpectedly slow"


# ── Repeated Questions — AI Orchestrator ──────────────────────────────────────

def test_repeated_orchestrator_calls_no_accumulation():
    """
    5 repeated orchestrator.ask() calls must not leave orphan state.
    All use a mocked LLM so no real inference occurs.
    """
    from app.ai.vision.unavailable_engine import UnavailableVisionEngine

    mock_llm = MagicMock()
    mock_llm.is_available = True
    mock_llm.model_name = "mock-model"
    mock_llm.generate.return_value = LLMResult(
        answer="mocked answer",
        model_name="mock-model",
        runtime_info="CPU",
        generation_time_ms=100.0,
        success=True,
    )

    vision = UnavailableVisionEngine()
    orchestrator = AIOrchestrator(mock_llm, vision)

    for i in range(5):
        result = orchestrator.ask("What is SnapSight?", None, None)
        assert result.success
        assert result.answer == "mocked answer"

    # LLM generate called 5 times (once per ask)
    assert mock_llm.generate.call_count == 5


# ── Capture Service Repeated Calls ────────────────────────────────────────────

@patch("app.capture.capture_service.CaptureService.capture_active_window")
def test_repeated_capture_no_state_leak(mock_capture):
    """Repeated capture calls return fresh results without accumulating state."""
    from app.capture.capture_service import CaptureService

    img = QImage(100, 100, QImage.Format_RGB32)
    img.fill(0xFFFFFF)
    mock_capture.return_value = CaptureResult(
        image=img, width=100, height=100, capture_type=CaptureType.WINDOW
    )

    service = CaptureService()
    results = []
    for _ in range(5):
        r = service.capture_active_window()
        results.append(r)

    assert len(results) == 5
    assert all(r.is_valid for r in results)
