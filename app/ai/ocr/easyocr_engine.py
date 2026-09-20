"""
EasyOCR engine implementation.
"""
import logging
import numpy as np
from PySide6.QtGui import QImage
from app.ai.ocr.engine import OCREngine
from app.ai.ocr.models import OCRTextRegion

logger = logging.getLogger(__name__)

class EasyOCREngine(OCREngine):
    def __init__(self):
        self._reader = None

    @property
    def engine_name(self) -> str:
        return "EasyOCR (PyTorch)"

    def _initialize_reader(self):
        """Lazily initialize the reader to avoid heavy startup and handle missing deps."""
        if self._reader is not None:
            return
            
        try:
            import easyocr
            # We enforce CPU-only for Sprint 3 to match the architectural constraints safely
            # download_enabled=False prevents silent downloads after first run, 
            # but for initial usage we must allow it or the user must pre-download.
            # We will let it download on first run, but log heavily.
            logger.info("Initializing EasyOCR. This may download models on first run.")
            self._reader = easyocr.Reader(['en'], gpu=False)
        except ImportError:
            logger.error("EasyOCR is not installed.")
            raise RuntimeError("OCR is unavailable because EasyOCR is not installed.")
        except Exception as e:
            logger.error(f"Failed to initialize EasyOCR: {e}")
            raise RuntimeError(f"Failed to initialize OCR models: {e}")

    def _qimage_to_numpy(self, image: QImage) -> np.ndarray:
        """Convert a QImage to a numpy array for EasyOCR."""
        image = image.convertToFormat(QImage.Format_RGB888)
        width = image.width()
        height = image.height()
        
        ptr = image.bits()
        # ptr is a memoryview in PySide6
        arr = np.array(ptr).reshape((height, width, 3))
        return arr

    def process_image(self, image: QImage) -> list[OCRTextRegion]:
        self._initialize_reader()
        
        try:
            np_img = self._qimage_to_numpy(image)
            
            # detail=1 gives us bounding box, text, and confidence
            results = self._reader.readtext(np_img, detail=1)
            
            regions = []
            for bbox, text, prob in results:
                # bbox is [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
                # Extract simple bounding box
                xs = [pt[0] for pt in bbox]
                ys = [pt[1] for pt in bbox]
                x = int(min(xs))
                y = int(min(ys))
                w = int(max(xs) - x)
                h = int(max(ys) - y)
                
                regions.append(OCRTextRegion(
                    text=text,
                    confidence=float(prob),
                    x=x, y=y, width=w, height=h
                ))
                
            return regions
            
        except Exception as e:
            logger.error(f"Error during EasyOCR processing: {e}")
            raise RuntimeError(f"OCR processing failed: {e}")
