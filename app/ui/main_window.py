"""
SnapSight Main Window — Sprint 7.
Coordinates capture → OCR → context → local LLM question answering with modern UX.
"""
import logging
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QMessageBox, QSplitter, QFrame
)
from PySide6.QtCore import Qt, QRect, QThread
from PySide6.QtGui import QPixmap, QShortcut, QKeySequence

from app.runtime.device_detector import DeviceDetector
from app.capture.capture_service import CaptureService, CaptureException
from app.capture.models import CaptureResult, CaptureState
from app.ui.components.region_selector import RegionSelector
from app.ai.ocr.ocr_service import OCRService
from app.ai.ocr.models import OCRResult
from app.ai.llm.llamacpp_engine import LlamaCppEngine
from app.ui.workers.ocr_worker import OCRWorker
from app.ai.vision.unavailable_engine import UnavailableVisionEngine
from app.ai.orchestrator import AIOrchestrator, AIOrchestratorResult
from app.ui.workers.ai_worker import AIWorker
from app.ui.styles import MODERN_DARK_THEME

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SnapSight")
        self.setMinimumSize(1000, 750)
        self.setStyleSheet(MODERN_DARK_THEME)

        # Services
        self.detector = DeviceDetector()
        self.capture_service = CaptureService()
        self.capture_state = CaptureState.NONE
        self.ocr_service = OCRService()
        self.llm_engine = LlamaCppEngine()
        self.vision_engine = UnavailableVisionEngine()
        self.orchestrator = AIOrchestrator(self.llm_engine, self.vision_engine)

        # State
        self._last_capture_result = None
        self._last_ocr_result = None
        self._ai_generating = False

        # Worker handles
        self._ocr_thread = None
        self._ocr_worker = None
        self._ai_thread = None
        self._ai_worker = None

        # Build UI
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(16)

        self.setup_header()
        self.setup_main_area()
        self.setup_footer()
        
        # Setup Shortcuts
        self.setup_shortcuts()

    # ── UI Setup ──────────────────────────────────────────────────────────────

    def setup_header(self):
        header_layout = QHBoxLayout()

        title_layout = QVBoxLayout()
        title_label = QLabel("SnapSight")
        title_label.setProperty("class", "Title")
        subtitle_label = QLabel("Private Screen Intelligence")
        subtitle_label.setProperty("class", "Subtitle")
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        title_layout.setSpacing(0)

        self.privacy_label = QLabel("🔒 On-device")
        self.privacy_label.setProperty("class", "StatusGreen")
        self.privacy_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        header_layout.addWidget(self.privacy_label)
        self.main_layout.addLayout(header_layout)

    def setup_main_area(self):
        splitter = QSplitter(Qt.Horizontal)

        # ── Left: Screen Context Card ──────────────────────────────────────────
        left_card = QFrame()
        left_card.setProperty("class", "Card")
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(12)

        context_title = QLabel("SCREEN CONTEXT")
        context_title.setProperty("class", "Metadata")
        left_layout.addWidget(context_title)

        self.preview_label = QLabel("Capture your screen to give SnapSight context.")
        self.preview_label.setProperty("class", "PreviewEmpty")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(280)
        self.preview_label.setSizePolicy(
            self.preview_label.sizePolicy().Policy.Expanding,
            self.preview_label.sizePolicy().Policy.Expanding,
        )

        self.metadata_label = QLabel("Waiting for screen capture")
        self.metadata_label.setProperty("class", "Metadata")
        self.metadata_label.setAlignment(Qt.AlignCenter)

        capture_btn_layout = QHBoxLayout()
        self.btn_capture_window = QPushButton("📷 Capture Window")
        self.btn_select_region = QPushButton("✂️ Select Region")
        self.btn_capture_window.clicked.connect(self.on_capture_window_clicked)
        self.btn_select_region.clicked.connect(self.on_select_region_clicked)
        capture_btn_layout.addWidget(self.btn_capture_window)
        capture_btn_layout.addWidget(self.btn_select_region)

        left_layout.addWidget(self.preview_label, stretch=1)
        left_layout.addWidget(self.metadata_label)
        left_layout.addLayout(capture_btn_layout)

        # ── Right: AI Interaction Cards ────────────────────────────────────────────
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(16)

        # Ask AI Card
        ask_card = QFrame()
        ask_card.setProperty("class", "Card")
        ask_layout = QVBoxLayout(ask_card)
        ask_layout.setContentsMargins(16, 16, 16, 16)
        
        ask_title = QLabel("ASK ABOUT YOUR SCREEN")
        ask_title.setProperty("class", "Metadata")
        
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("What would you like to know?\n(e.g., 'Summarize this screen', 'What does this error mean?')\nYou can also ask general questions without a capture.")
        self.text_input.setMaximumHeight(80)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_ask_ai = QPushButton("Ask AI")
        self.btn_ask_ai.setProperty("class", "Primary")
        self.btn_ask_ai.setMinimumWidth(100)
        self.btn_ask_ai.clicked.connect(self.on_ask_ai_clicked)
        btn_layout.addWidget(self.btn_ask_ai)

        ask_layout.addWidget(ask_title)
        ask_layout.addWidget(self.text_input)
        ask_layout.addLayout(btn_layout)

        # Answer Card
        answer_card = QFrame()
        answer_card.setProperty("class", "Card")
        answer_layout = QVBoxLayout(answer_card)
        answer_layout.setContentsMargins(16, 16, 16, 16)

        ans_title = QLabel("ANSWER")
        ans_title.setProperty("class", "Metadata")

        self.answer_text_edit = QTextEdit()
        self.answer_text_edit.setReadOnly(True)
        self.answer_text_edit.setPlaceholderText("Your answer will appear here.")
        self.answer_text_edit.setStyleSheet("border: none; background: transparent;")

        self.ai_metadata_label = QLabel("")
        self.ai_metadata_label.setProperty("class", "Metadata")

        answer_layout.addWidget(ans_title)
        answer_layout.addWidget(self.answer_text_edit, stretch=1)
        answer_layout.addWidget(self.ai_metadata_label)

        right_layout.addWidget(ask_card)
        right_layout.addWidget(answer_card, stretch=1)

        splitter.addWidget(left_card)
        splitter.addWidget(right_widget)
        splitter.setSizes([480, 520])

        self.main_layout.addWidget(splitter, stretch=1)

    def setup_footer(self):
        footer_layout = QHBoxLayout()

        privacy_msg = QLabel("🔒 Screen data stays on this device.")
        privacy_msg.setProperty("class", "Metadata")

        llm_avail = self.llm_engine._runtime.available
        llm_status = f"LLM: llama.cpp • {'CPU' if llm_avail else 'Unavailable'}"
        
        ocr_exec = self.ocr_service._runtime_status.execution
        if ocr_exec.available:
            ocr_backend = self.ocr_service._runtime_status.backend
            ocr_accel = ocr_exec.accelerator.value
            if ocr_backend == "easyocr":
                ocr_backend = "EasyOCR"
            elif ocr_backend == "qualcomm":
                ocr_backend = "Qualcomm"
            ocr_status = f"OCR: {ocr_backend} • {ocr_accel}"
        else:
            ocr_status = "OCR: Unavailable"

        telemetry_label = QLabel(f"{ocr_status}  |  {llm_status}")
        telemetry_label.setProperty("class", "Metadata")
        telemetry_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        footer_layout.addWidget(privacy_msg)
        footer_layout.addStretch()
        footer_layout.addWidget(telemetry_label)
        self.main_layout.addLayout(footer_layout)

    def setup_shortcuts(self):
        # Ctrl+Enter to Ask AI
        shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        shortcut.activated.connect(self.on_ask_ai_clicked)

    # ── Capture Flow ──────────────────────────────────────────────────────────

    def set_capture_state(self, state: CaptureState):
        self.capture_state = state
        capturing = (state == CaptureState.CAPTURING)
        self.btn_capture_window.setEnabled(not capturing)
        self.btn_select_region.setEnabled(not capturing)
        if capturing:
            self.preview_label.setText("Analyzing screen...")
            self.preview_label.setProperty("class", "PreviewEmpty")
            self.preview_label.style().unpolish(self.preview_label)
            self.preview_label.style().polish(self.preview_label)
            
            self.metadata_label.setText("Reading screen...")
            self._last_capture_result = None
            self._last_ocr_result = None
            self._update_ask_ai_state()

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
            if self.preview_label.text() == "Analyzing screen...":
                self.preview_label.setText(
                    "Capture your screen to give SnapSight context." if not hasattr(self, "current_pixmap") else ""
                )
                self.metadata_label.setText(
                    "Waiting for screen capture" if not hasattr(self, "current_pixmap") else "Screen context ready"
                )
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
        self._last_capture_result = result
        pixmap = QPixmap.fromImage(result.image)
        self.current_pixmap = pixmap
        
        # Remove dashed border on success
        self.preview_label.setProperty("class", "PreviewImage")
        self.preview_label.style().unpolish(self.preview_label)
        self.preview_label.style().polish(self.preview_label)
        
        self.update_preview()

        import datetime
        time_str = datetime.datetime.fromtimestamp(result.timestamp).strftime("%H:%M:%S")
        self.metadata_label.setText(f"Screen captured | {result.width}×{result.height} | {time_str}")
        
        self.start_ocr_processing(result)

    def handle_capture_error(self, message: str):
        self.set_capture_state(CaptureState.FAILED)
        QMessageBox.warning(self, "Capture Failed", f"SnapSight couldn't capture the screen: {message}\nPlease try again.")
        if self.preview_label.text() == "Analyzing screen...":
            self.preview_label.setText(
                "Capture your screen to give SnapSight context." if not hasattr(self, "current_pixmap") else ""
            )
            self.preview_label.setProperty("class", "PreviewEmpty")
            self.preview_label.style().unpolish(self.preview_label)
            self.preview_label.style().polish(self.preview_label)
            self.metadata_label.setText("Waiting for screen capture")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "current_pixmap") and self.capture_state == CaptureState.SUCCESS:
            self.update_preview()

    def update_preview(self):
        if hasattr(self, "current_pixmap") and not self.current_pixmap.isNull():
            scaled = self.current_pixmap.scaled(
                self.preview_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self.preview_label.setPixmap(scaled)

    # ── OCR Flow ──────────────────────────────────────────────────────────────

    def start_ocr_processing(self, capture_result: CaptureResult):
        if not self.ocr_service.is_available:
            self.metadata_label.setText("OCR Unavailable")
            return

        self.metadata_label.setText("Reading screen...")

        self._ocr_thread = QThread()
        self._ocr_worker = OCRWorker(capture_result, self.ocr_service)
        self._ocr_worker.moveToThread(self._ocr_thread)

        self._ocr_thread.started.connect(self._ocr_worker.process)
        self._ocr_worker.finished.connect(self.on_ocr_success)
        self._ocr_worker.error.connect(self.on_ocr_error)

        self._ocr_worker.finished.connect(self._ocr_thread.quit)
        self._ocr_worker.finished.connect(self._ocr_worker.deleteLater)
        self._ocr_thread.finished.connect(self._ocr_thread.deleteLater)
        self._ocr_worker.error.connect(self._ocr_thread.quit)
        self._ocr_worker.error.connect(self._ocr_worker.deleteLater)

        self._ocr_thread.start()

    def on_ocr_success(self, result: OCRResult):
        self.metadata_label.setText(f"Screen context ready ({len(result.regions)} regions)")
        # Save result for orchestrator
        self._last_ocr_result = result
        self._update_ask_ai_state()

    def on_ocr_error(self, error_msg: str):
        self.metadata_label.setText("Couldn’t read text from this capture.")
        logger.error(f"OCR Error: {error_msg}")
        self._last_ocr_result = None
        self._update_ask_ai_state()

    # ── Orchestrator Flow ─────────────────────────────────────────────────────

    def _update_ask_ai_state(self):
        """Enable Ask AI when no generation is running."""
        self.btn_ask_ai.setEnabled(not self._ai_generating)

    def on_ask_ai_clicked(self):
        question = self.text_input.toPlainText().strip()
        if not question:
            return

        if self._ai_generating:
            return  # Ignore duplicate clicks

        self._start_ai_generation(question)

    def _start_ai_generation(self, question: str):
        self._ai_generating = True
        self._update_ask_ai_state()
        self.btn_ask_ai.setText("Thinking...")
        self.ai_metadata_label.setText("")
        self.answer_text_edit.clear()

        self._ai_thread = QThread()
        self._ai_worker = AIWorker(question, self._last_capture_result, self._last_ocr_result, self.orchestrator)
        self._ai_worker.moveToThread(self._ai_thread)

        self._ai_thread.started.connect(self._ai_worker.process)
        self._ai_worker.finished.connect(self.on_ai_success)
        self._ai_worker.error.connect(self.on_ai_error)

        self._ai_worker.finished.connect(self._ai_thread.quit)
        self._ai_worker.finished.connect(self._ai_worker.deleteLater)
        self._ai_thread.finished.connect(self._ai_thread.deleteLater)
        self._ai_worker.error.connect(self._ai_thread.quit)
        self._ai_worker.error.connect(self._ai_worker.deleteLater)

        self._ai_thread.start()

    def on_ai_success(self, result: AIOrchestratorResult):
        self._ai_generating = False
        self.btn_ask_ai.setText("Ask AI")
        self._update_ask_ai_state()

        if not result.success:
            self._show_ai_error(result.error or "Unknown error")
            return

        gen_s = result.inference_time_ms / 1000.0
        self.ai_metadata_label.setText(f"Route: {result.route_used.name} • Backend: {result.backend_used} • Time: {gen_s:.1f}s")
        self.answer_text_edit.setPlainText(result.answer)

    def on_ai_error(self, error_msg: str):
        self._ai_generating = False
        self.btn_ask_ai.setText("Ask AI")
        self._update_ask_ai_state()
        self._show_ai_error(error_msg)

    def _show_ai_error(self, message: str):
        user_msg = "SnapSight couldn't generate an answer. Please try again."
        if "model" in message.lower() and "found" in message.lower():
            user_msg = "Local AI model not found.\nPlace the required model in the models folder and try again."
        elif "vision" in message.lower() and "unavailable" in message.lower():
            user_msg = "Visual understanding isn't available on this device yet.\nText-based screen understanding is still available."
            
        self.answer_text_edit.setPlainText(user_msg)
        self.ai_metadata_label.setText("Error encountered.")
        logger.error(f"AI error: {message}")
