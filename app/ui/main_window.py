"""
SnapSight Main Window.
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QTextEdit, QMessageBox
)
from PySide6.QtCore import Qt, QRect, QThread
from PySide6.QtGui import QPixmap, QImage
from app.runtime.device_detector import DeviceDetector
from app.capture.capture_service import CaptureService, CaptureException
from app.capture.models import CaptureResult, CaptureState
from app.ui.components.region_selector import RegionSelector
from app.ai.ocr.ocr_service import OCRService
from app.ai.ocr.models import OCRResult
from app.ui.workers.ocr_worker import OCRWorker
import logging

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SnapSight")
        self.setMinimumSize(900, 700)
        
        self.detector = DeviceDetector()
        self.capture_service = CaptureService()
        self.capture_state = CaptureState.NONE
        
        # Initialize OCR service (will safely fall back if not available)
        self.ocr_service = OCRService()
        
        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)
        
        self.setup_header()
        
        # Create a horizontal layout for the split view (Preview | OCR)
        self.split_layout = QHBoxLayout()
        self.setup_screen_context()
        self.setup_ocr_context()
        self.main_layout.addLayout(self.split_layout, stretch=1)
        
        self.setup_question_section()
        self.setup_footer()

    def setup_header(self):
        header_layout = QHBoxLayout()
        title_label = QLabel("<h2>SnapSight</h2>")
        
        status_label = QLabel("● Local AI")
        status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        status_label.setStyleSheet("color: gray;")
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(status_label)
        
        self.main_layout.addLayout(header_layout)

    def setup_screen_context(self):
        left_layout = QVBoxLayout()
        
        # Preview Area
        self.preview_label = QLabel("No screen captured")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("background-color: #e0e0e0; border-radius: 8px; color: #555;")
        self.preview_label.setMinimumHeight(300)
        self.preview_label.setSizePolicy(
            self.preview_label.sizePolicy().Policy.Expanding,
            self.preview_label.sizePolicy().Policy.Expanding
        )
        
        # Metadata label
        self.metadata_label = QLabel("")
        self.metadata_label.setStyleSheet("color: gray; font-size: 11px;")
        self.metadata_label.setAlignment(Qt.AlignCenter)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        self.btn_capture_window = QPushButton("Capture Window")
        self.btn_select_region = QPushButton("Select Region")
        
        self.btn_capture_window.clicked.connect(self.on_capture_window_clicked)
        self.btn_select_region.clicked.connect(self.on_select_region_clicked)
        
        buttons_layout.addWidget(self.btn_capture_window)
        buttons_layout.addWidget(self.btn_select_region)
        buttons_layout.addStretch()
        
        left_layout.addWidget(self.preview_label)
        left_layout.addWidget(self.metadata_label)
        left_layout.addLayout(buttons_layout)
        
        self.split_layout.addLayout(left_layout, stretch=1)
        
    def setup_ocr_context(self):
        right_layout = QVBoxLayout()
        
        self.ocr_status_label = QLabel("<b>OCR Status:</b> Idle")
        
        self.ocr_text_edit = QTextEdit()
        self.ocr_text_edit.setReadOnly(True)
        self.ocr_text_edit.setPlaceholderText("OCR results will appear here...")
        
        right_layout.addWidget(self.ocr_status_label)
        right_layout.addWidget(self.ocr_text_edit)
        
        self.split_layout.addLayout(right_layout, stretch=1)

    def setup_question_section(self):
        label = QLabel("<b>Ask anything about this screen</b>")
        self.main_layout.addWidget(label)
        
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Type your question here...")
        self.text_input.setMaximumHeight(80)
        self.main_layout.addWidget(self.text_input)
        
        self.btn_ask_ai = QPushButton("Ask AI")
        self.btn_ask_ai.setEnabled(False) # AI functionality is not implemented yet
        self.btn_ask_ai.setToolTip("AI functionality will be added in a later sprint.")
        self.main_layout.addWidget(self.btn_ask_ai, alignment=Qt.AlignRight)

    def setup_footer(self):
        footer_layout = QHBoxLayout()
        
        local_processing_label = QLabel("🔒 Local Processing")
        local_processing_label.setStyleSheet("color: #4CAF50;")
        
        hardware_mode = self.detector.detect()
        mode_label = QLabel(f"Hardware: {hardware_mode}")
        mode_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        mode_label.setStyleSheet("color: gray; font-size: 10px;")
        
        footer_layout.addWidget(local_processing_label)
        footer_layout.addStretch()
        footer_layout.addWidget(mode_label)
        
        self.main_layout.addLayout(footer_layout)

    def set_capture_state(self, state: CaptureState):
        self.capture_state = state
        if state == CaptureState.CAPTURING:
            self.btn_capture_window.setEnabled(False)
            self.btn_select_region.setEnabled(False)
            self.preview_label.setText("Capturing...")
            self.ocr_status_label.setText("<b>OCR Status:</b> Idle")
            self.ocr_text_edit.clear()
        else:
            self.btn_capture_window.setEnabled(True)
            self.btn_select_region.setEnabled(True)

    def on_capture_window_clicked(self):
        self.set_capture_state(CaptureState.CAPTURING)
        try:
            result = self.capture_service.capture_active_window()
            self.handle_capture_result(result)
        except CaptureException as e:
            self.handle_capture_error(str(e))
        except Exception as e:
            logger.error(f"Unexpected error in capture_window: {e}")
            self.handle_capture_error("An unexpected error occurred during capture.")

    def on_select_region_clicked(self):
        self.set_capture_state(CaptureState.CAPTURING)
        self.hide()
        
        self.selector = RegionSelector()
        self.selector.region_selected.connect(self.on_region_selected)
        self.selector.show()

    def on_region_selected(self, rect: QRect):
        self.show()
        self.raise_()
        self.activateWindow()
        
        if rect.isEmpty():
            self.set_capture_state(CaptureState.CANCELLED)
            if self.preview_label.text() == "Capturing...":
                self.preview_label.setText("No screen captured" if not hasattr(self, 'current_pixmap') else "")
            return
            
        try:
            result = self.capture_service.capture_region(rect)
            self.handle_capture_result(result)
        except CaptureException as e:
            self.handle_capture_error(str(e))
        except Exception as e:
            logger.error(f"Unexpected error in capture_region: {e}")
            self.handle_capture_error("An unexpected error occurred during region capture.")

    def handle_capture_result(self, result: CaptureResult):
        if not result.is_valid:
            self.handle_capture_error("Capture resulted in an invalid image.")
            return
            
        self.set_capture_state(CaptureState.SUCCESS)
        
        pixmap = QPixmap.fromImage(result.image)
        self.current_pixmap = pixmap
        self.update_preview()
        
        time_str = __import__('datetime').datetime.fromtimestamp(result.timestamp).strftime('%H:%M:%S')
        meta_text = f"Type: {result.capture_type.name} | Res: {result.width}x{result.height} | Time: {time_str}"
        self.metadata_label.setText(meta_text)
        
        self.start_ocr_processing(result)

    def handle_capture_error(self, message: str):
        self.set_capture_state(CaptureState.FAILED)
        QMessageBox.warning(self, "Capture Failed", message)
        
        if self.preview_label.text() == "Capturing...":
            if hasattr(self, 'current_pixmap'):
                self.update_preview()
            else:
                self.preview_label.setText("No screen captured")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'current_pixmap') and self.capture_state == CaptureState.SUCCESS:
            self.update_preview()

    def update_preview(self):
        if hasattr(self, 'current_pixmap') and not self.current_pixmap.isNull():
            scaled_pixmap = self.current_pixmap.scaled(
                self.preview_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.preview_label.setPixmap(scaled_pixmap)

    def start_ocr_processing(self, capture_result: CaptureResult):
        if not self.ocr_service.is_available:
            self.ocr_status_label.setText("<b>OCR Status:</b> Unavailable (EasyOCR not installed)")
            return
            
        self.ocr_status_label.setText("<b>OCR Status:</b> Reading screen...")
        
        # Threading using QObject and moveToThread
        self.ocr_thread = QThread()
        self.ocr_worker = OCRWorker(capture_result, self.ocr_service)
        self.ocr_worker.moveToThread(self.ocr_thread)
        
        # Connect signals
        self.ocr_thread.started.connect(self.ocr_worker.process)
        self.ocr_worker.finished.connect(self.on_ocr_success)
        self.ocr_worker.error.connect(self.on_ocr_error)
        
        # Cleanup
        self.ocr_worker.finished.connect(self.ocr_thread.quit)
        self.ocr_worker.finished.connect(self.ocr_worker.deleteLater)
        self.ocr_thread.finished.connect(self.ocr_thread.deleteLater)
        
        self.ocr_worker.error.connect(self.ocr_thread.quit)
        self.ocr_worker.error.connect(self.ocr_worker.deleteLater)
        
        self.ocr_thread.start()

    def on_ocr_success(self, result: OCRResult):
        region_count = len(result.regions)
        self.ocr_status_label.setText(
            f"<b>OCR Status:</b> {region_count} text regions detected · {result.processing_time_ms:.0f} ms"
        )
        
        self.ocr_text_edit.setPlainText(result.full_text)
        
    def on_ocr_error(self, error_msg: str):
        self.ocr_status_label.setText(f"<b>OCR Status:</b> Error")
        self.ocr_text_edit.setPlainText(f"Failed to extract text:\n{error_msg}")
