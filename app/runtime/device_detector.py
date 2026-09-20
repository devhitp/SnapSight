"""
Minimal hardware detection abstraction.
"""

class DeviceDetector:
    def __init__(self):
        pass
        
    def detect(self) -> str:
        """
        Detect the current device hardware.
        Returns 'UNKNOWN' or 'COMPATIBILITY_MODE' safely for Sprint 1.
        """
        return "COMPATIBILITY_MODE"
