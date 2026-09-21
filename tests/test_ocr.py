"""
Tests for the OCR pipeline and fallbacks.
"""
import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtGui import QImage
from app.ai.ocr.models import OCRResult, OCRTextRegion
from app.ai.ocr.runtime import AccelerationType, RuntimeStatus, HardwareIdentity, RuntimeCapabilities, ExecutionState
from app.ai.ocr.ocr_service import OCRService
from app.capture.models import CaptureResult, CaptureType

def _mock_hardware() -> HardwareIdentity:
    return HardwareIdentity("Windows", "AMD64", "Intel", "Core i7")

def _mock_runtime() -> RuntimeCapabilities:
    return RuntimeCapabilities("PyTorch", "1.0", "CPU")

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
    assert status.execution.available is False
    assert status.execution.accelerator == AccelerationType.NONE
    assert status.backend == "unsupported"

@patch('app.ai.ocr.runtime._detect_vendor_and_device')
@patch('app.ai.ocr.runtime.importlib.util.find_spec')
def test_runtime_detection_with_easyocr(mock_find_spec, mock_vendor):
    """Test runtime detection when easyocr is available."""
    mock_find_spec.return_value = True # Simulate module exists
    mock_vendor.return_value = ("Intel", "Core")
    from app.ai.ocr.runtime import detect_runtime
    
    status = detect_runtime()
    assert status.execution.available is True
    assert status.backend == "easyocr"
    assert status.execution.accelerator == AccelerationType.CPU

@patch('app.ai.ocr.ocr_service.detect_runtime')
@patch('app.ai.ocr.ocr_service.EasyOCREngine')
def test_ocr_service_processing_easyocr(mock_engine_cls, mock_detect):
    """Test the OCRService orchestration without real engine."""
    mock_detect.return_value = RuntimeStatus(
        hardware=_mock_hardware(),
        runtime=_mock_runtime(),
        execution=ExecutionState(True, AccelerationType.CPU, "Available"),
        backend="easyocr"
    )
    
    mock_engine = MagicMock()
    mock_engine.engine_name = "EasyOCR"
    mock_engine.process_image.return_value = [
        OCRTextRegion("MockText", 0.9, 0, 0, 10, 10)
    ]
    mock_engine_cls.return_value = mock_engine
    
    service = OCRService()
    assert service.is_available is True
    assert service._runtime_status.backend == "easyocr"
    
    # Fake capture
    img = QImage(100, 100, QImage.Format_RGB32)
    capture = CaptureResult(image=img, width=100, height=100, capture_type=CaptureType.FULLSCREEN)
    
    result = service.process_capture(capture)
    
    assert result.engine_name == "EasyOCR"
    assert "EasyOCR" in result.runtime_info
    assert "CPU" in result.runtime_info
    assert len(result.regions) == 1
    assert result.regions[0].text == "MockText"
    assert result.processing_time_ms >= 0

@patch('app.ai.ocr.ocr_service.detect_runtime')
@patch('app.ai.ocr.ocr_service.QualcommOCREngine')
@patch('app.ai.ocr.ocr_service.EasyOCREngine')
def test_ocr_service_fallback_when_qualcomm_fails(mock_easyocr_cls, mock_qualcomm_cls, mock_detect):
    """Test OCR fallback mechanism from Qualcomm to EasyOCR."""
    # detect_runtime says qualcomm is discoverable
    mock_detect.return_value = RuntimeStatus(
        hardware=_mock_hardware(),
        runtime=_mock_runtime(),
        execution=ExecutionState(False, AccelerationType.NPU, "Not yet verified"),
        backend="qualcomm"
    )
    
    # Qualcomm initialization fails
    mock_qualcomm_cls.side_effect = RuntimeError("No model found")
    
    # EasyOCR mock
    mock_easy_engine = MagicMock()
    mock_easy_engine.engine_name = "EasyOCR"
    mock_easyocr_cls.return_value = mock_easy_engine
    
    service = OCRService()
    
    # Should fallback to EasyOCR
    assert service.is_available is True
    assert service._runtime_status.backend == "easyocr"
    assert service._runtime_status.execution.accelerator == AccelerationType.CPU
    assert service._engine == mock_easy_engine

@patch('app.ai.ocr.ocr_service.detect_runtime')
def test_ocr_service_unavailable(mock_detect):
    """Test that OCRService fails gracefully when unavailable."""
    mock_detect.return_value = RuntimeStatus(
        hardware=_mock_hardware(),
        runtime=_mock_runtime(),
        execution=ExecutionState(False, AccelerationType.NONE, "Unavailable"),
        backend="unsupported"
    )
    
    service = OCRService()
    assert service.is_available is False
    
    img = QImage(100, 100, QImage.Format_RGB32)
    capture = CaptureResult(image=img, width=100, height=100, capture_type=CaptureType.FULLSCREEN)
    
    with pytest.raises(RuntimeError, match="OCR service is currently unavailable."):
        service.process_capture(capture)
