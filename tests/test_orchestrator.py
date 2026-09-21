import pytest
from unittest.mock import MagicMock
from app.ai.orchestrator import AIOrchestrator
from app.ai.router.models import QuestionIntent
from app.ai.llm.models import LLMResult
from app.ai.vision.models import VisionResult
from app.capture.models import CaptureResult, CaptureType
from PySide6.QtGui import QImage

@pytest.fixture
def mock_llm_engine():
    engine = MagicMock()
    engine.is_available = True
    engine.model_name = "MockLLM"
    engine.generate.return_value = LLMResult(
        answer="LLM Answer",
        model_name="MockLLM",
        runtime_info="CPU",
        generation_time_ms=100.0,
        success=True
    )
    return engine

@pytest.fixture
def mock_vision_engine():
    engine = MagicMock()
    engine.is_available = True
    engine.engine_name = "MockVision"
    engine.analyze_image.return_value = VisionResult(
        answer="Vision Answer",
        backend="MockVision",
        success=True,
        inference_time_ms=200.0
    )
    return engine

@pytest.fixture
def dummy_capture():
    img = QImage(10, 10, QImage.Format_RGB32)
    return CaptureResult(
        image=img,
        width=10,
        height=10,
        capture_type=CaptureType.FULLSCREEN,
        timestamp=0.0
    )

def test_orchestrator_general_question(mock_llm_engine, mock_vision_engine):
    orchestrator = AIOrchestrator(mock_llm_engine, mock_vision_engine)
    result = orchestrator.ask("What is recursion?", None, None)
    
    assert result.success
    assert result.route_used == QuestionIntent.GENERAL
    assert result.backend_used == "Local LLM (MockLLM)"
    assert result.answer == "LLM Answer"
    assert not result.ocr_used
    assert not result.vision_used
    mock_llm_engine.generate.assert_called_once()
    mock_vision_engine.analyze_image.assert_not_called()

def test_orchestrator_visual_question(mock_llm_engine, mock_vision_engine, dummy_capture):
    orchestrator = AIOrchestrator(mock_llm_engine, mock_vision_engine)
    result = orchestrator.ask("What color is this?", dummy_capture, None)
    
    assert result.success
    assert result.route_used == QuestionIntent.VISUAL
    assert result.backend_used == "MockVision"
    assert result.answer == "Vision Answer"
    assert not result.ocr_used
    assert result.vision_used
    mock_vision_engine.analyze_image.assert_called_once()
    mock_llm_engine.generate.assert_not_called()

def test_orchestrator_missing_capture_for_vision(mock_llm_engine, mock_vision_engine):
    orchestrator = AIOrchestrator(mock_llm_engine, mock_vision_engine)
    result = orchestrator.ask("What color is this?", None, None)
    
    assert not result.success
    assert "No valid screen capture" in result.error
    assert result.route_used == QuestionIntent.VISUAL
