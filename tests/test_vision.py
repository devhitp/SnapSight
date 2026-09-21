import pytest
from PySide6.QtGui import QImage
from app.ai.vision.unavailable_engine import UnavailableVisionEngine

def test_unavailable_vision_engine():
    engine = UnavailableVisionEngine()
    assert not engine.is_available
    assert engine.engine_name == "UnavailableVisionEngine"
    
    # Create a dummy image
    img = QImage(100, 100, QImage.Format_RGB32)
    
    result = engine.analyze_image(img, "What is this?")
    assert result.success
    assert "unavailable" in result.answer.lower()
    assert result.backend == "Unavailable"
    assert result.confidence == 1.0
    assert result.inference_time_ms > 0
