from dataclasses import dataclass
from enum import Enum, auto

class VisionBackend(Enum):
    UNAVAILABLE = auto()
    LOCAL_CPU = auto()
    LOCAL_NPU = auto()
    LOCAL_GPU = auto()
    
@dataclass
class VisionRuntimeStatus:
    available: bool
    backend: VisionBackend
    detail: str = ""

def detect_vision_runtime() -> VisionRuntimeStatus:
    """
    Detect if a suitable local vision runtime is available.
    Currently hardcoded to unavailable for Sprint 5 due to hardware constraints.
    """
    return VisionRuntimeStatus(
        available=False,
        backend=VisionBackend.UNAVAILABLE,
        detail="No local vision backend installed on this machine."
    )
