"""
SnapSight Main Window.
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QTextEdit, QMessageBox
)
from PySide6.QtCore import Qt
from app.runtime.device_detector import DeviceDetector

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SnapSight")
        self.setMinimumSize(800, 600)
        
        self.detector = DeviceDetector()
        
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
        self.preview_label = QLabel("No screen captured")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("background-color: #e0e0e0; border-radius: 8px; color: #555;")
        self.preview_label.setMinimumHeight(300)
        
        buttons_layout = QHBoxLayout()
        self.btn_capture_window = QPushButton("Capture Window")
        self.btn_select_region = QPushButton("Select Region")
        
        # Connect buttons to show informational message
        self.btn_capture_window.clicked.connect(self.show_sprint2_message)
        self.btn_select_region.clicked.connect(self.show_sprint2_message)
        
        buttons_layout.addWidget(self.btn_capture_window)
        buttons_layout.addWidget(self.btn_select_region)
        buttons_layout.addStretch()
        
        self.main_layout.addWidget(self.preview_label)
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

    def show_sprint2_message(self):
        QMessageBox.information(self, "Coming Soon", "Screen capture will be implemented in Sprint 2.")
