"""
OCR Runtime reporting and detection.
"""
import importlib.util
import platform
import os
import logging
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class AccelerationType(Enum):
    CPU = "CPU"
    NPU = "NPU"
    NONE = "None"
    UNKNOWN = "Unknown"

@dataclass
class HardwareIdentity:
    platform: str
    architecture: str
    vendor: str
    device: str

@dataclass
class RuntimeCapabilities:
    runtime_name: str
    runtime_version: str
    provider: str

@dataclass
class ExecutionState:
    available: bool
    accelerator: AccelerationType
    reason: str

@dataclass
class RuntimeStatus:
    hardware: HardwareIdentity
    runtime: RuntimeCapabilities
    execution: ExecutionState
    backend: str = "unsupported"

def _detect_vendor_and_device() -> tuple[str, str]:
    vendor = "Unknown"
    device = "Unknown"
    if platform.system() == "Windows":
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            proc_name, _ = winreg.QueryValueEx(key, "ProcessorNameString")
            vendor_id, _ = winreg.QueryValueEx(key, "VendorIdentifier")
            winreg.CloseKey(key)
            
            proc_name_lower = proc_name.lower()
            if "snapdragon" in proc_name_lower or "qualcomm" in proc_name_lower:
                vendor = "Qualcomm"
            elif "intel" in proc_name_lower or "genuineintel" in vendor_id.lower():
                vendor = "Intel"
            elif "amd" in proc_name_lower or "authenticamd" in vendor_id.lower():
                vendor = "AMD"
                
            device = proc_name.strip()
        except Exception:
            # Fallback
            proc_id = os.environ.get("PROCESSOR_IDENTIFIER", "").lower()
            if "snapdragon" in proc_id or "qualcomm" in proc_id:
                vendor = "Qualcomm"
                device = proc_id
            elif "intel" in proc_id or "genuineintel" in proc_id:
                vendor = "Intel"
                device = proc_id
            elif "amd" in proc_id or "authenticamd" in proc_id:
                vendor = "AMD"
                device = proc_id
            else:
                device = platform.processor()
                proc_str = device.lower()
                if "intel" in proc_str:
                    vendor = "Intel"
                elif "amd" in proc_str:
                    vendor = "AMD"
    else:
        device = platform.processor()
        
    return vendor, device

def detect_runtime() -> RuntimeStatus:
    system = platform.system()
    arch = platform.machine()
    vendor, device = _detect_vendor_and_device()
    
    hardware = HardwareIdentity(
        platform=system,
        architecture=arch,
        vendor=vendor,
        device=device
    )
    
    runtime_name = "None"
    runtime_version = "None"
    provider = "None"
    
    # Check for ONNX Runtime
    has_ort = importlib.util.find_spec("onnxruntime") is not None
    qnn_discoverable = False
    
    if has_ort:
        try:
            import onnxruntime as ort
            runtime_name = "ONNX Runtime"
            runtime_version = ort.__version__
            if "QNNExecutionProvider" in ort.get_available_providers():
                qnn_discoverable = True
                provider = "QNNExecutionProvider"
        except Exception as e:
            logger.warning(f"Failed to inspect onnxruntime: {e}")

    # Note: discovering QNN is not verifying execution. 
    # Actual QualcommOCREngine will verify execution before confirming 'available' = True.
    # detect_runtime() only checks what is discoverable without loading models.
    
    has_easyocr = importlib.util.find_spec("easyocr") is not None

    if vendor == "Qualcomm" and qnn_discoverable:
        # Architecture is ready for Qualcomm, but model/execution must be verified by the engine.
        runtime = RuntimeCapabilities(runtime_name, runtime_version, provider)
        execution = ExecutionState(available=False, accelerator=AccelerationType.NPU, reason="QNN discoverable but model execution not yet verified")
        return RuntimeStatus(hardware, runtime, execution, backend="qualcomm")
        
    if has_easyocr:
        # EasyOCR (PyTorch CPU) fallback
        runtime = RuntimeCapabilities("PyTorch", "Unknown", "CPU")
        execution = ExecutionState(available=True, accelerator=AccelerationType.CPU, reason="PyTorch/EasyOCR CPU fallback available")
        return RuntimeStatus(hardware, runtime, execution, backend="easyocr")

    runtime = RuntimeCapabilities(runtime_name, runtime_version, provider)
    execution = ExecutionState(available=False, accelerator=AccelerationType.NONE, reason="No compatible OCR runtime found")
    
    return RuntimeStatus(hardware, runtime, execution)
