"""
Screen capture service.
Provides full screen, active window, and region capture functionality.
"""
import sys
import platform
import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QScreen, QImage
from PySide6.QtCore import QRect
from app.capture.models import CaptureResult, CaptureType

logger = logging.getLogger(__name__)

class CaptureException(Exception):
    """Exception raised for capture-specific errors."""
    pass

class CaptureService:
    def __init__(self):
        pass

    def capture_fullscreen(self) -> CaptureResult:
        """Capture the primary screen."""
        try:
            screen = QApplication.primaryScreen()
            if not screen:
                raise CaptureException("No primary screen detected.")
                
            pixmap = screen.grabWindow(0)
            if pixmap.isNull():
                raise CaptureException("Failed to grab screen window.")
                
            image = pixmap.toImage()
            return CaptureResult(
                image=image,
                width=image.width(),
                height=image.height(),
                capture_type=CaptureType.FULLSCREEN,
                metadata={"screen": screen.name()}
            )
        except Exception as e:
            logger.error(f"Fullscreen capture failed: {e}")
            raise CaptureException(f"Fullscreen capture failed: {e}")

    def capture_region(self, rect: QRect) -> CaptureResult:
        """Capture a specific region of the virtual desktop screen."""
        try:
            if not rect.isValid() or rect.isEmpty():
                raise CaptureException("Invalid or empty capture region.")

            # Find the screen containing this rect, or default to primary
            screen = QApplication.screenAt(rect.center())
            if not screen:
                screen = QApplication.primaryScreen()

            if not screen:
                raise CaptureException("No screen detected for the selected region.")

            pixmap = screen.grabWindow(0, rect.x(), rect.y(), rect.width(), rect.height())
            
            if pixmap.isNull():
                raise CaptureException("Failed to grab screen region.")
                
            image = pixmap.toImage()
            return CaptureResult(
                image=image,
                width=image.width(),
                height=image.height(),
                capture_type=CaptureType.REGION,
                metadata={
                    "x": rect.x(),
                    "y": rect.y(),
                    "screen": screen.name()
                }
            )
        except Exception as e:
            logger.error(f"Region capture failed: {e}")
            raise CaptureException(f"Region capture failed: {e}")

    def capture_active_window(self) -> CaptureResult:
        """Capture the currently active foreground window using Windows API."""
        if platform.system() != "Windows":
            raise CaptureException("Active window capture is only implemented for Windows in this sprint.")
            
        try:
            import ctypes
            from ctypes.wintypes import RECT
            
            # Get the foreground window handle
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            if not hwnd:
                raise CaptureException("Could not identify the active window.")
                
            # Get window bounds
            rect = RECT()
            if not ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                raise CaptureException("Could not get bounds of the active window.")
                
            x, y = rect.left, rect.top
            width = rect.right - rect.left
            height = rect.bottom - rect.top
            
            # Add simple safety checks
            if width <= 0 or height <= 0:
                raise CaptureException("Active window has invalid dimensions.")
                
            qrect = QRect(x, y, width, height)
            result = self.capture_region(qrect)
            result.capture_type = CaptureType.WINDOW
            
            # Attempt to get window title for metadata
            try:
                length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
                    result.metadata["window_title"] = buff.value
            except Exception:
                pass # Safe to ignore if title extraction fails
                
            return result
            
        except CaptureException:
            raise
        except Exception as e:
            logger.error(f"Active window capture failed: {e}")
            raise CaptureException(f"Active window capture failed: {e}")
