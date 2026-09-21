"""
Tests for hardware detection and runtime status modeling.
Simulated/mock capability tests.
"""
import pytest
from unittest.mock import patch, MagicMock

from app.ai.ocr.runtime import (
    detect_runtime, 
    _detect_vendor_and_device,
    AccelerationType,
    RuntimeStatus
)

def test_detect_vendor_intel_windows():
    """Simulated/mock capability test for Intel x86-64."""
    with patch("platform.system", return_value="Windows"), \
         patch("os.environ.get", return_value="Intel64 Family 6 Model 141 Stepping 1, GenuineIntel"):
        
        # We mock winreg import failure to test the fallback os.environ behavior
        with patch.dict("sys.modules", {"winreg": None}):
            vendor, device = _detect_vendor_and_device()
            
            assert vendor == "Intel"
            assert "intel" in device.lower()

def test_detect_vendor_qualcomm_windows():
    """Simulated/mock capability test for Qualcomm Snapdragon on Windows."""
    with patch("platform.system", return_value="Windows"), \
         patch("os.environ.get", return_value="Snapdragon(R) X Elite - X1E78100"):
        
        with patch.dict("sys.modules", {"winreg": None}):
            vendor, device = _detect_vendor_and_device()
            
            assert vendor == "Qualcomm"
            assert "snapdragon" in device.lower()

@patch("app.ai.ocr.runtime._detect_vendor_and_device")
@patch("app.ai.ocr.runtime.importlib.util.find_spec")
def test_detect_runtime_intel_easyocr(mock_find_spec, mock_vendor):
    """Simulated/mock capability test: Intel machine with EasyOCR."""
    mock_vendor.return_value = ("Intel", "Core i5")
    
    def side_effect(name):
        return MagicMock() if name == "easyocr" else None
    mock_find_spec.side_effect = side_effect
    
    with patch("platform.system", return_value="Windows"), \
         patch("platform.machine", return_value="AMD64"):
        
        status = detect_runtime()
        
        assert status.hardware.vendor == "Intel"
        assert status.backend == "easyocr"
        assert status.execution.accelerator == AccelerationType.CPU
        assert status.execution.available is True

@patch("app.ai.ocr.runtime._detect_vendor_and_device")
@patch("app.ai.ocr.runtime.importlib.util.find_spec")
def test_detect_runtime_qualcomm_no_ort(mock_find_spec, mock_vendor):
    """Simulated/mock capability test: Qualcomm machine, but ONNX not installed."""
    mock_vendor.return_value = ("Qualcomm", "Snapdragon X Elite")
    
    def side_effect(name):
        return MagicMock() if name == "easyocr" else None
    mock_find_spec.side_effect = side_effect
    
    with patch("platform.system", return_value="Windows"), \
         patch("platform.machine", return_value="ARM64"):
        
        status = detect_runtime()
        
        assert status.hardware.vendor == "Qualcomm"
        # Should fallback to easyocr because ORT is missing
        assert status.backend == "easyocr"
        assert status.execution.accelerator == AccelerationType.CPU
        assert status.execution.available is True

@patch("app.ai.ocr.runtime._detect_vendor_and_device")
@patch("app.ai.ocr.runtime.importlib.util.find_spec")
def test_detect_runtime_qualcomm_ort_no_qnn(mock_find_spec, mock_vendor):
    """Simulated/mock capability test: Qualcomm machine, ORT installed, but NO QNN provider."""
    mock_vendor.return_value = ("Qualcomm", "Snapdragon")
    mock_find_spec.return_value = MagicMock() # both easyocr and onnxruntime exist
    
    # Mock onnxruntime module
    mock_ort = MagicMock()
    mock_ort.__version__ = "1.18.0"
    mock_ort.get_available_providers.return_value = ["CPUExecutionProvider"]
    
    with patch("platform.system", return_value="Windows"), \
         patch("platform.machine", return_value="ARM64"), \
         patch.dict("sys.modules", {"onnxruntime": mock_ort}):
        
        status = detect_runtime()
        
        assert status.hardware.vendor == "Qualcomm"
        # QNN not available, fallback to easyocr
        assert status.backend == "easyocr"
        assert status.execution.accelerator == AccelerationType.CPU

@patch("app.ai.ocr.runtime._detect_vendor_and_device")
@patch("app.ai.ocr.runtime.importlib.util.find_spec")
def test_detect_runtime_qualcomm_ort_with_qnn(mock_find_spec, mock_vendor):
    """Simulated/mock capability test: Qualcomm machine, ORT installed AND QNN available."""
    mock_vendor.return_value = ("Qualcomm", "Snapdragon")
    mock_find_spec.return_value = MagicMock()
    
    mock_ort = MagicMock()
    mock_ort.__version__ = "1.18.0"
    mock_ort.get_available_providers.return_value = ["QNNExecutionProvider", "CPUExecutionProvider"]
    
    with patch("platform.system", return_value="Windows"), \
         patch("platform.machine", return_value="ARM64"), \
         patch.dict("sys.modules", {"onnxruntime": mock_ort}):
        
        status = detect_runtime()
        
        assert status.hardware.vendor == "Qualcomm"
        # Architecture ready for Qualcomm!
        assert status.backend == "qualcomm"
        assert status.execution.accelerator == AccelerationType.NPU
        # detect_runtime only checks discoverability. The engine verifies execution.
        assert status.execution.available is False
        assert "not yet verified" in status.execution.reason
