"""
SnapSight Main Window.
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QTextEdit, QMessageBox
)
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPixmap, QImage
from app.runtime.device_detector import DeviceDetector
from app.capture.capture_service import CaptureService, CaptureException
from app.capture.models import CaptureResult, CaptureState
from app.ui.components.region_selector import RegionSelector
import logging

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SnapSight")
        self.setMinimumSize(800, 600)
        
        self.detector = DeviceDetector()
        self.capture_service = CaptureService()
        self.capture_state = CaptureState.NONE
        
        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)
        
        self.setup_header()
        self.setup_screen_context()
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
        # Preview Area
        self.preview_label = QLabel("No screen captured")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("background-color: #e0e0e0; border-radius: 8px; color: #555;")
        self.preview_label.setMinimumHeight(300)
        # Allows label to resize nicely
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
        
        self.main_layout.addWidget(self.preview_label)
        self.main_layout.addWidget(self.metadata_label)
        self.main_layout.addLayout(buttons_layout)
        
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
        
        # Hide the main window to allow clean region selection of what's behind it
        self.hide()
        
        self.selector = RegionSelector()
        self.selector.region_selected.connect(self.on_region_selected)
        self.selector.show()

    def on_region_selected(self, rect: QRect):
        # Restore the main window
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
        
        # Convert QImage to QPixmap at the UI boundary
        pixmap = QPixmap.fromImage(result.image)
        self.current_pixmap = pixmap
        
        self.update_preview()
        
        # Show metadata
        time_str = __import__('datetime').datetime.fromtimestamp(result.timestamp).strftime('%H:%M:%S')
        meta_text = f"Type: {result.capture_type.name} | Res: {result.width}x{result.height} | Time: {time_str}"
        self.metadata_label.setText(meta_text)

    def handle_capture_error(self, message: str):
        self.set_capture_state(CaptureState.FAILED)
        QMessageBox.warning(self, "Capture Failed", message)
        
        # Reset preview if it was showing "Capturing..."
        if self.preview_label.text() == "Capturing...":
            if hasattr(self, 'current_pixmap'):
                self.update_preview()
            else:
                self.preview_label.setText("No screen captured")

    def resizeEvent(self, event):
        """Ensure the preview image scales when the window resizes."""
        super().resizeEvent(event)
        if hasattr(self, 'current_pixmap') and self.capture_state == CaptureState.SUCCESS:
            self.update_preview()

    def update_preview(self):
        if hasattr(self, 'current_pixmap') and not self.current_pixmap.isNull():
            # Scale the pixmap to fit the label, preserving aspect ratio
            scaled_pixmap = self.current_pixmap.scaled(
                self.preview_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.preview_label.setPixmap(scaled_pixmap)
