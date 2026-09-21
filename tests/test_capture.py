"""
Tests for Sprint 2 Capture Pipeline.
"""
import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QImage, QMouseEvent
from PySide6.QtWidgets import QApplication
from app.capture.models import CaptureResult, CaptureType, CaptureState
from app.capture.capture_service import CaptureService, CaptureException
from app.ui.components.region_selector import RegionSelector
from app.ui.main_window import MainWindow

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app

def test_capture_result_model():
    """Test CaptureResult dataclass."""
    img = QImage(100, 100, QImage.Format_RGB32)
    result = CaptureResult(
        image=img,
        width=100,
        height=100,
        capture_type=CaptureType.REGION
    )
    assert result.is_valid is True
    assert result.width == 100
    assert result.capture_type == CaptureType.REGION
    
    # Test invalid
    invalid_img = QImage()
    invalid_result = CaptureResult(image=invalid_img, width=0, height=0, capture_type=CaptureType.UNKNOWN)
    assert invalid_result.is_valid is False

@patch('app.capture.capture_service.QApplication')
def test_capture_fullscreen(mock_qapp):
    """Test full screen capture via service."""
    service = CaptureService()
    mock_screen = MagicMock()
    mock_pixmap = MagicMock()
    mock_image = QImage(1920, 1080, QImage.Format_RGB32)
    
    mock_pixmap.isNull.return_value = False
    mock_pixmap.toImage.return_value = mock_image
    mock_screen.grabWindow.return_value = mock_pixmap
    mock_screen.name.return_value = "Screen1"
    
    mock_qapp.primaryScreen.return_value = mock_screen
    
    result = service.capture_fullscreen()
    assert result.is_valid is True
    assert result.capture_type == CaptureType.FULLSCREEN
    assert result.metadata["screen"] == "Screen1"

def test_region_selector_cancel(qapp):
    """Test that RegionSelector safely emits empty QRect on Escape."""
    selector = RegionSelector()
    
    # Mock the signal to track emissions
    mock_slot = MagicMock()
    selector.region_selected.connect(mock_slot)
    
    selector.cancel_selection()
    
    mock_slot.assert_called_once()
    emitted_rect = mock_slot.call_args[0][0]
    assert emitted_rect.isEmpty()

@patch('app.ui.main_window.OCRService')
@patch('app.capture.capture_service.CaptureService.capture_active_window')
def test_ui_capture_window_success(mock_capture_active, mock_ocr_service_cls, qapp, qtbot):
    """Test that the main window updates UI when Capture Window is clicked and succeeds."""
    mock_ocr = MagicMock()
    mock_ocr.is_available = False
    mock_ocr_service_cls.return_value = mock_ocr

    window = MainWindow()
    qtbot.addWidget(window)
    
    # Setup mock result
    mock_image = QImage(800, 600, QImage.Format_RGB32)
    mock_result = CaptureResult(image=mock_image, width=800, height=600, capture_type=CaptureType.WINDOW, timestamp=1234567.0)
    mock_capture_active.return_value = mock_result
    
    qtbot.mouseClick(window.btn_capture_window, Qt.LeftButton)
    
    # Verify state updated
    assert window.capture_state == CaptureState.SUCCESS
    assert "OCR Unavailable" in window.metadata_label.text()
    assert hasattr(window, 'current_pixmap')
    assert not window.current_pixmap.isNull()

@patch('app.ui.main_window.OCRService')
@patch('app.capture.capture_service.CaptureService.capture_active_window')
def test_ui_capture_window_failure(mock_capture_active, mock_ocr_service_cls, qapp, qtbot):
    """Test that the main window handles exceptions cleanly."""
    mock_ocr = MagicMock()
    mock_ocr.is_available = False
    mock_ocr_service_cls.return_value = mock_ocr

    window = MainWindow()
    qtbot.addWidget(window)
    
    # Setup mock to raise exception
    mock_capture_active.side_effect = CaptureException("Simulated error")
    
    # We patch QMessageBox to avoid it blocking the test
    with patch('app.ui.main_window.QMessageBox.warning') as mock_warning:
        qtbot.mouseClick(window.btn_capture_window, Qt.LeftButton)
        mock_warning.assert_called_once()
        
    assert window.capture_state == CaptureState.FAILED
    assert window.preview_label.text() == "Capture your screen to give SnapSight context."
