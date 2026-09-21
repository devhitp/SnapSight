"""
Benchmark utility for OCR execution (CPU vs Qualcomm).
"""
import sys
import os
import time
from typing import Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from app.ai.ocr.runtime import detect_runtime
from app.ai.ocr.ocr_service import OCRService
from app.capture.models import CaptureResult, CaptureType

def create_test_image(width: int = 1920, height: int = 1080) -> QImage:
    """Create a blank white image for benchmarking overhead, since we can't bundle real screens easily."""
    img = QImage(width, height, QImage.Format_RGB32)
    img.fill(0xFFFFFF)
    return img

def run_benchmark():
    app = QApplication.instance() or QApplication(sys.argv)
    
    print("=== SnapSight OCR Benchmark ===")
    
    # 1. Hardware & Runtime Identity
    status = detect_runtime()
    
    print(f"Machine:      {status.hardware.vendor} {status.hardware.device} ({status.hardware.architecture})")
    print(f"Platform:     {status.hardware.platform}")
    
    # We instantiate OCRService to get the actual selector
    service = OCRService()
    active_status = service._runtime_status
    
    backend_name = "Unknown"
    if service.is_available:
        backend_name = service._engine.engine_name
        
    print(f"Backend:      {backend_name}")
    print(f"Runtime:      {active_status.runtime.runtime_name} ({active_status.runtime.runtime_version})")
    print(f"Provider:     {active_status.runtime.provider}")
    print(f"Accelerator:  {active_status.execution.accelerator.value}")
    print(f"Model:        hrnet_w48_ocr.onnx (Expected) / EasyOCR builtin" if active_status.backend == "qualcomm" else "EasyOCR default")
    print(f"Status:       {'READY' if service.is_available else 'UNAVAILABLE'} - {active_status.execution.reason}")
    print("-" * 31)

    if not service.is_available:
        print("Cannot run benchmark: OCR service is unavailable.")
        return

    # 2. Run iterations
    iterations = 3
    resolutions = [(1920, 1080), (800, 600)]
    
    for w, h in resolutions:
        print(f"\nBenchmarking {w}x{h}...")
        
        # Warmup
        test_img = create_test_image(w, h)
        capture = CaptureResult(image=test_img, width=w, height=h, capture_type=CaptureType.FULLSCREEN)
        
        try:
            # We don't have separate preprocess/inference hooks in our engine API right now, 
            # we just measure total OCR time.
            service.process_capture(capture)
            
            total_time = 0.0
            
            for i in range(iterations):
                start = time.perf_counter()
                res = service.process_capture(capture)
                duration_ms = (time.perf_counter() - start) * 1000
                total_time += duration_ms
                print(f"  Run {i+1}: {duration_ms:.1f} ms | Regions: {len(res.regions)}")
                
            avg_time = total_time / iterations
            print(f"  -> Average Total Time: {avg_time:.1f} ms")
            print(f"  -> Success")
        except Exception as e:
            print(f"  -> Failure: {e}")

if __name__ == "__main__":
    run_benchmark()
