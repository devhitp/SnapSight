"""
Tests for the OCR pipeline.
"""
import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtGui import QImage
from app.ai.ocr.models import OCRResult, OCRTextRegion
from app.ai.ocr.runtime import RuntimeBackend, AccelerationType, RuntimeStatus
from app.ai.ocr.ocr_service import OCRService
from app.capture.models import CaptureResult, CaptureType

def test_ocr_result_model():
    """Test OCR text combination helper."""
    regions = [
        OCRTextRegion("Hello", 0.99, 10, 10, 50, 20),
        OCRTextRegion("World", 0.98, 10, 40, 50, 20)
    ]
    result = OCRResult(
        regions=regions,
        image_width=800,
        image_height=600,
        processing_time_ms=150.0,
        engine_name="TestEngine",
        runtime_info="CPU"
    )
    assert result.full_text == "Hello\nWorld"

@patch('app.ai.ocr.runtime.importlib.util.find_spec')
def test_runtime_detection_without_easyocr(mock_find_spec):
    """Test runtime detection when easyocr is missing."""
    mock_find_spec.return_value = None
    from app.ai.ocr.runtime import detect_runtime
    
    status = detect_runtime()
    assert status.available is False
    assert status.backend == RuntimeBackend.UNKNOWN
    assert status.acceleration == AccelerationType.UNKNOWN

@patch('app.ai.ocr.runtime.importlib.util.find_spec')
def test_runtime_detection_with_easyocr(mock_find_spec):
    """Test runtime detection when easyocr is available."""
    mock_find_spec.return_value = True # Simulate module exists
    from app.ai.ocr.runtime import detect_runtime
    
    status = detect_runtime()
    assert status.available is True
    assert status.backend == RuntimeBackend.PYTORCH
    assert status.acceleration == AccelerationType.CPU

@patch('app.ai.ocr.ocr_service.detect_runtime')
@patch('app.ai.ocr.ocr_service.EasyOCREngine')
def test_ocr_service_processing(mock_engine_cls, mock_detect):
    """Test the OCRService orchestration without real engine."""
    mock_detect.return_value = RuntimeStatus(
        backend=RuntimeBackend.PYTORCH, 
        acceleration=AccelerationType.CPU, 
        available=True
    )
    
    mock_engine = MagicMock()
    mock_engine.engine_name = "MockEngine"
    mock_engine.process_image.return_value = [
        OCRTextRegion("MockText", 0.9, 0, 0, 10, 10)
    ]
    mock_engine_cls.return_value = mock_engine
    
    service = OCRService()
    assert service.is_available is True
    
    # Fake capture
    img = QImage(100, 100, QImage.Format_RGB32)
    capture = CaptureResult(image=img, width=100, height=100, capture_type=CaptureType.FULLSCREEN)
    
    result = service.process_capture(capture)
    
    assert result.engine_name == "MockEngine"
    assert "PyTorch" in result.runtime_info
    assert "CPU" in result.runtime_info
    assert len(result.regions) == 1
    assert result.regions[0].text == "MockText"
    assert result.processing_time_ms >= 0

@patch('app.ai.ocr.ocr_service.detect_runtime')
def test_ocr_service_unavailable(mock_detect):
    """Test that OCRService fails gracefully when unavailable."""
    mock_detect.return_value = RuntimeStatus(
        backend=RuntimeBackend.UNKNOWN, 
        acceleration=AccelerationType.UNKNOWN, 
        available=False
    )
    
    service = OCRService()
    assert service.is_available is False
    
    img = QImage(100, 100, QImage.Format_RGB32)
    capture = CaptureResult(image=img, width=100, height=100, capture_type=CaptureType.FULLSCREEN)
    
    with pytest.raises(RuntimeError, match="OCR service is currently unavailable."):
        service.process_capture(capture)
