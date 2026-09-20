"""
OCR Runtime reporting and detection.
"""
import importlib.util
from enum import Enum, auto
from dataclasses import dataclass

class RuntimeBackend(Enum):
    PYTORCH = "PyTorch"
    ONNX_RUNTIME = "ONNX Runtime"
    ONNX_RUNTIME_QNN = "ONNX Runtime + QNN"
    UNKNOWN = "Unknown"

class AccelerationType(Enum):
    CPU = "CPU"
    NPU = "NPU"
    UNKNOWN = "Unknown"

@dataclass
class RuntimeStatus:
    backend: RuntimeBackend
    acceleration: AccelerationType
    available: bool

def detect_runtime() -> RuntimeStatus:
    """
    Safely detects the current runtime availability without crashing.
    In Sprint 3, we only officially support the PyTorch/EasyOCR CPU path, 
    but we architecturally prepare for ONNX/QNN.
    """
    # Check for easyocr
    has_easyocr = importlib.util.find_spec("easyocr") is not None
    
    if not has_easyocr:
        return RuntimeStatus(
            backend=RuntimeBackend.UNKNOWN,
            acceleration=AccelerationType.UNKNOWN,
            available=False
        )
        
    # We are using EasyOCR's default PyTorch backend for this sprint.
    return RuntimeStatus(
        backend=RuntimeBackend.PYTORCH,
        acceleration=AccelerationType.CPU,
        available=True
    )
