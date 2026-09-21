"""
Sprint 4 Tests — Local LLM & Screen Question Answering.
All tests use mocked engines. No real GGUF model required.
"""
import pytest
import time
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from app.ai.ocr.models import OCRResult, OCRTextRegion
from app.ai.context.builder import ContextBuilder, CONFIDENCE_THRESHOLD, MAX_CONTEXT_CHARS
from app.ai.llm.models import LLMResult
from app.ai.orchestrator import AIOrchestratorResult
from app.ai.router.models import QuestionIntent
from app.ai.llm.runtime import LLMBackend, LLMAcceleration, LLMRuntimeStatus
from app.capture.models import CaptureType


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


# ─── LLMResult Model Tests ────────────────────────────────────────────────────

def test_llm_result_success():
    r = LLMResult(
        answer="SnapSight is a screen assistant.",
        model_name="test-model.gguf",
        runtime_info="llama.cpp (CPU)",
        generation_time_ms=1500.0,
        success=True,
        prompt_tokens=50,
        generated_tokens=12,
    )
    assert r.success
    assert r.answer == "SnapSight is a screen assistant."
    assert r.tokens_per_sec is not None
    assert r.tokens_per_sec > 0


def test_llm_result_failure_factory():
    r = LLMResult.failure("Model file not found.", model_name="phi.gguf")
    assert not r.success
    assert r.error == "Model file not found."
    assert r.answer == ""
    assert r.tokens_per_sec is None


def test_llm_result_no_tokens():
    """tokens_per_sec should return None when token counts are unavailable."""
    r = LLMResult(
        answer="hello",
        model_name="test",
        runtime_info="cpu",
        generation_time_ms=800.0,
        success=True,
    )
    assert r.tokens_per_sec is None


# ─── ContextBuilder Tests ─────────────────────────────────────────────────────

def _make_ocr_result(regions):
    return OCRResult(
        regions=regions,
        image_width=1920,
        image_height=1080,
        processing_time_ms=200.0,
        engine_name="TestEngine",
        runtime_info="CPU",
    )


def test_context_builder_basic():
    regions = [
        OCRTextRegion("SnapSight", 0.95, 10, 10, 100, 20),
        OCRTextRegion("Deadline: September 30", 0.90, 10, 40, 200, 20),
    ]
    result = _make_ocr_result(regions)
    ctx = ContextBuilder().build(result)
    assert "SnapSight" in ctx
    assert "Deadline: September 30" in ctx


def test_context_builder_filters_low_confidence():
    regions = [
        OCRTextRegion("Good text", 0.90, 0, 0, 100, 20),
        OCRTextRegion("Noise", CONFIDENCE_THRESHOLD - 0.01, 0, 30, 50, 20),
    ]
    result = _make_ocr_result(regions)
    ctx = ContextBuilder().build(result)
    assert "Good text" in ctx
    assert "Noise" not in ctx


def test_context_builder_empty_ocr():
    result = _make_ocr_result([])
    ctx = ContextBuilder().build(result)
    assert ctx == ""


def test_context_builder_reading_order():
    """Regions should be sorted top-to-bottom, left-to-right."""
    regions = [
        OCRTextRegion("Second line", 0.95, 0, 50, 100, 20),
        OCRTextRegion("First line", 0.95, 0, 10, 100, 20),
    ]
    result = _make_ocr_result(regions)
    ctx = ContextBuilder().build(result)
    assert ctx.index("First line") < ctx.index("Second line")


def test_context_builder_truncates_long_context():
    long_text = "A" * (MAX_CONTEXT_CHARS + 500)
    regions = [OCRTextRegion(long_text, 0.95, 0, 0, 100, 20)]
    result = _make_ocr_result(regions)
    ctx = ContextBuilder().build(result)
    assert len(ctx) <= MAX_CONTEXT_CHARS


def test_context_builder_format_for_prompt_wraps_context():
    cb = ContextBuilder()
    formatted = cb.format_for_prompt("Some text")
    assert "BEGIN SCREEN TEXT" in formatted
    assert "END SCREEN TEXT" in formatted
    assert "Some text" in formatted


def test_context_builder_format_for_prompt_empty():
    cb = ContextBuilder()
    formatted = cb.format_for_prompt("")
    assert "No screen text" in formatted


def test_context_builder_whitespace_normalization():
    regions = [OCRTextRegion("Hello   World  \t  Here", 0.95, 0, 0, 100, 20)]
    result = _make_ocr_result(regions)
    ctx = ContextBuilder().build(result)
    assert "Hello World Here" in ctx


# ─── Runtime Detection Tests ──────────────────────────────────────────────────

@patch("app.ai.llm.runtime.importlib.util.find_spec")
def test_llm_runtime_without_llama_cpp(mock_find_spec):
    mock_find_spec.return_value = None
    from app.ai.llm.runtime import detect_llm_runtime
    status = detect_llm_runtime()
    assert not status.available
    assert status.backend == LLMBackend.UNKNOWN


@patch("app.ai.llm.runtime.importlib.util.find_spec")
def test_llm_runtime_with_llama_cpp(mock_find_spec):
    mock_find_spec.return_value = True
    from app.ai.llm.runtime import detect_llm_runtime
    status = detect_llm_runtime()
    assert status.available
    assert status.backend == LLMBackend.LLAMA_CPP
    assert status.acceleration == LLMAcceleration.CPU


# ─── LlamaCppEngine (mocked) Tests ────────────────────────────────────────────

@patch("app.ai.llm.llamacpp_engine.detect_llm_runtime")
def test_engine_missing_model_file(mock_runtime):
    mock_runtime.return_value = LLMRuntimeStatus(
        backend=LLMBackend.LLAMA_CPP,
        acceleration=LLMAcceleration.CPU,
        available=True,
    )
    from app.ai.llm.llamacpp_engine import LlamaCppEngine
    engine = LlamaCppEngine(model_path="models/nonexistent.gguf")
    result = engine.generate("What is this?", "Some context")
    assert not result.success
    assert "not found" in result.error.lower()


@patch("app.ai.llm.llamacpp_engine.detect_llm_runtime")
def test_engine_llama_cpp_unavailable(mock_runtime):
    mock_runtime.return_value = LLMRuntimeStatus(
        backend=LLMBackend.UNKNOWN,
        acceleration=LLMAcceleration.UNKNOWN,
        available=False,
        detail="not installed",
    )
    from app.ai.llm.llamacpp_engine import LlamaCppEngine
    engine = LlamaCppEngine(model_path="models/any.gguf")
    result = engine.generate("Test?", "context")
    assert not result.success
    assert "not installed" in result.error.lower()


def test_engine_empty_question():
    """Engine should reject empty questions before even loading the model."""
    from app.ai.llm.llamacpp_engine import LlamaCppEngine
    with patch("app.ai.llm.llamacpp_engine.detect_llm_runtime") as mock_runtime:
        mock_runtime.return_value = LLMRuntimeStatus(
            backend=LLMBackend.LLAMA_CPP,
            acceleration=LLMAcceleration.CPU,
            available=True,
        )
        engine = LlamaCppEngine(model_path="models/fake.gguf")
        # Inject a fake loaded model so _initialize returns None
        engine._llm = MagicMock()

        result = engine.generate("", "Some context")
        assert not result.success
        assert "empty" in result.error.lower()


# ─── UI Tests ─────────────────────────────────────────────────────────────────

@patch("app.ui.main_window.OCRService")
@patch("app.ui.main_window.LlamaCppEngine")
def test_ask_ai_enabled_on_start(mock_llm_cls, mock_ocr_cls, qapp):
    mock_ocr_cls.return_value.is_available = False
    mock_llm_cls.return_value._runtime.available = False
    from app.ui.main_window import MainWindow
    window = MainWindow()
    assert window.btn_ask_ai.isEnabled()


@patch("app.ui.main_window.OCRService")
@patch("app.ui.main_window.LlamaCppEngine")
def test_ask_ai_remains_enabled_after_ocr_context(mock_llm_cls, mock_ocr_cls, qapp):
    mock_ocr_cls.return_value.is_available = False
    mock_llm_cls.return_value._runtime.available = False
    from app.ui.main_window import MainWindow
    window = MainWindow()

    # Simulate receiving OCR context
    window._last_ocr_result = "mock_result"
    window._ai_generating = False
    window._update_ask_ai_state()

    assert window.btn_ask_ai.isEnabled()


@patch("app.ui.main_window.OCRService")
@patch("app.ui.main_window.LlamaCppEngine")
def test_ask_ai_disabled_while_generating(mock_llm_cls, mock_ocr_cls, qapp):
    mock_ocr_cls.return_value.is_available = False
    mock_llm_cls.return_value._runtime.available = False
    from app.ui.main_window import MainWindow
    window = MainWindow()

    window._last_ocr_result = "mock_result"
    window._ai_generating = True
    window._update_ask_ai_state()

    assert not window.btn_ask_ai.isEnabled()


@patch("app.ui.main_window.OCRService")
@patch("app.ui.main_window.LlamaCppEngine")
def test_ai_success_updates_ui(mock_llm_cls, mock_ocr_cls, qapp):
    mock_ocr_cls.return_value.is_available = False
    mock_llm_cls.return_value._runtime.available = False
    from app.ui.main_window import MainWindow
    window = MainWindow()

    window._ai_generating = True
    mock_result = AIOrchestratorResult(
        answer="SnapSight is a local screen assistant.",
        route_used=QuestionIntent.GENERAL,
        backend_used="Local LLM",
        inference_time_ms=2500.0,
        ocr_used=False,
        vision_used=False,
        success=True
    )
    window.on_ai_success(mock_result)

    assert not window._ai_generating
    assert "SnapSight" in window.answer_text_edit.toPlainText()
    assert "2.5s" in window.ai_metadata_label.text()


@patch("app.ui.main_window.OCRService")
@patch("app.ui.main_window.LlamaCppEngine")
def test_ai_failure_updates_ui(mock_llm_cls, mock_ocr_cls, qapp):
    mock_ocr_cls.return_value.is_available = False
    mock_llm_cls.return_value._runtime.available = False
    from app.ui.main_window import MainWindow
    window = MainWindow()

    window._ai_generating = True
    window.on_ai_error("Model file not found.")

    assert not window._ai_generating
    assert "not found" in window.answer_text_edit.toPlainText().lower()
    assert "Error encountered" in window.ai_metadata_label.text()
