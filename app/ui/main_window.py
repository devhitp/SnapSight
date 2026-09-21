"""
SnapSight Main Window — Sprint 4.
Coordinates capture → OCR → context → local LLM question answering.
"""
import logging
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QMessageBox, QSplitter
)
from PySide6.QtCore import Qt, QRect, QThread
from PySide6.QtGui import QPixmap

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

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SnapSight")
        self.setMinimumSize(1000, 750)

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

        # Worker handles (kept alive while threads run)
        self._ocr_thread = None
        self._ocr_worker = None
        self._ai_thread = None
        self._ai_worker = None

        # Build UI
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(12)

        self.setup_header()
        self.setup_main_area()
        self.setup_question_section()
        self.setup_footer()

    # ── UI Setup ──────────────────────────────────────────────────────────────

    def setup_header(self):
        header_layout = QHBoxLayout()

        title_label = QLabel("<h2>SnapSight</h2>")

        llm_avail = self.llm_engine._runtime.available
        llm_status = f"LLM: llama.cpp • {'CPU' if llm_avail else 'Unavailable'}"
        
        ocr_exec = self.ocr_service._runtime_status.execution
        if ocr_exec.available:
            ocr_backend = self.ocr_service._runtime_status.backend
            ocr_accel = ocr_exec.accelerator.value
            # Display nicer name for easyocr
            if ocr_backend == "easyocr":
                ocr_backend = "EasyOCR"
            elif ocr_backend == "qualcomm":
                ocr_backend = "Qualcomm"
            ocr_status = f"OCR: {ocr_backend} • {ocr_accel}"
        else:
            ocr_status = "OCR: Unavailable"

        self.header_status_label = QLabel(f"🔒 {ocr_status}  |  {llm_status}")
        self.header_status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.header_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.header_status_label)
        self.main_layout.addLayout(header_layout)

    def setup_main_area(self):
        splitter = QSplitter(Qt.Horizontal)

        # ── Left: Capture Preview ──────────────────────────────────────────
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.preview_label = QLabel("No screen captured")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet(
            "background-color: #2b2b2b; border-radius: 8px; color: #888; font-size: 13px;"
        )
        self.preview_label.setMinimumHeight(280)
        self.preview_label.setSizePolicy(
            self.preview_label.sizePolicy().Policy.Expanding,
            self.preview_label.sizePolicy().Policy.Expanding,
        )

        self.metadata_label = QLabel("")
        self.metadata_label.setStyleSheet("color: gray; font-size: 10px;")
        self.metadata_label.setAlignment(Qt.AlignCenter)

        capture_btn_layout = QHBoxLayout()
        self.btn_capture_window = QPushButton("📷  Capture Window")
        self.btn_select_region = QPushButton("✂️  Select Region")
        self.btn_capture_window.clicked.connect(self.on_capture_window_clicked)
        self.btn_select_region.clicked.connect(self.on_select_region_clicked)
        capture_btn_layout.addWidget(self.btn_capture_window)
        capture_btn_layout.addWidget(self.btn_select_region)
        capture_btn_layout.addStretch()

        left_layout.addWidget(self.preview_label)
        left_layout.addWidget(self.metadata_label)
        left_layout.addLayout(capture_btn_layout)

        # ── Right: OCR & Answer ────────────────────────────────────────────
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.ocr_status_label = QLabel("<b>OCR:</b> Idle")
        self.ocr_text_edit = QTextEdit()
        self.ocr_text_edit.setReadOnly(True)
        self.ocr_text_edit.setPlaceholderText("Screen text will appear here after capture...")
        self.ocr_text_edit.setMaximumHeight(180)

        self.ai_status_label = QLabel("<b>AI:</b> No context yet")
        self.ai_status_label.setStyleSheet("color: gray; font-size: 11px;")
        self.answer_text_edit = QTextEdit()
        self.answer_text_edit.setReadOnly(True)
        self.answer_text_edit.setPlaceholderText("Answer will appear here...")

        right_layout.addWidget(self.ocr_status_label)
        right_layout.addWidget(self.ocr_text_edit)
        right_layout.addWidget(self.ai_status_label)
        right_layout.addWidget(self.answer_text_edit)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([480, 520])

        self.main_layout.addWidget(splitter, stretch=1)

    def setup_question_section(self):
        question_label = QLabel("<b>Ask anything about your captured screen</b>")
        self.main_layout.addWidget(question_label)

        question_input_layout = QHBoxLayout()
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Ask anything about your captured screen...")
        self.text_input.setMaximumHeight(60)

        self.btn_ask_ai = QPushButton("Ask AI")
        self.btn_ask_ai.setEnabled(True)
        self.btn_ask_ai.setMinimumWidth(90)
        self.btn_ask_ai.setToolTip("Ask a question about the screen or a general question.")
        self.btn_ask_ai.clicked.connect(self.on_ask_ai_clicked)

        question_input_layout.addWidget(self.text_input)
        question_input_layout.addWidget(self.btn_ask_ai)
        self.main_layout.addLayout(question_input_layout)

    def setup_footer(self):
        footer_layout = QHBoxLayout()

        privacy_label = QLabel("🔒 All processing is local · No data leaves this device")
        privacy_label.setStyleSheet("color: #4CAF50; font-size: 10px;")

        hw_mode = self.detector.detect()
        hw_label = QLabel(f"Hardware: {hw_mode}")
        hw_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        hw_label.setStyleSheet("color: gray; font-size: 10px;")

        footer_layout.addWidget(privacy_label)
        footer_layout.addStretch()
        footer_layout.addWidget(hw_label)
        self.main_layout.addLayout(footer_layout)

    # ── Capture Flow ──────────────────────────────────────────────────────────

    def set_capture_state(self, state: CaptureState):
        self.capture_state = state
        capturing = (state == CaptureState.CAPTURING)
        self.btn_capture_window.setEnabled(not capturing)
        self.btn_select_region.setEnabled(not capturing)
        if capturing:
            self.preview_label.setText("Capturing...")
            self.ocr_status_label.setText("<b>OCR:</b> Idle")
            self.ocr_text_edit.clear()
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
            if self.preview_label.text() == "Capturing...":
                self.preview_label.setText(
                    "No screen captured" if not hasattr(self, "current_pixmap") else ""
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
        self.update_preview()

        import datetime
        time_str = datetime.datetime.fromtimestamp(result.timestamp).strftime("%H:%M:%S")
        self.metadata_label.setText(
            f"Type: {result.capture_type.name} | {result.width}×{result.height} | {time_str}"
        )
        self.start_ocr_processing(result)

    def handle_capture_error(self, message: str):
        self.set_capture_state(CaptureState.FAILED)
        QMessageBox.warning(self, "Capture Failed", message)
        if self.preview_label.text() == "Capturing...":
            self.preview_label.setText(
                "No screen captured" if not hasattr(self, "current_pixmap") else ""
            )

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
            self.ocr_status_label.setText("<b>OCR:</b> Unavailable (EasyOCR not installed)")
            return

        self.ocr_status_label.setText("<b>OCR:</b> Reading screen...")

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
        n = len(result.regions)
        self.ocr_status_label.setText(
            f"<b>OCR:</b> {n} region{'s' if n != 1 else ''} detected · {result.processing_time_ms:.0f} ms"
        )
        self.ocr_text_edit.setPlainText(result.full_text)

        # Save result for orchestrator
        self._last_ocr_result = result
        self._update_ask_ai_state()

    def on_ocr_error(self, error_msg: str):
        self.ocr_status_label.setText("<b>OCR:</b> Error")
        self.ocr_text_edit.setPlainText(f"Failed to extract text:\n{error_msg}")
        self._last_ocr_result = None
        self._update_ask_ai_state()

    # ── Orchestrator Flow ─────────────────────────────────────────────────────

    def _update_ask_ai_state(self):
        """Enable Ask AI when no generation is running."""
        self.btn_ask_ai.setEnabled(not self._ai_generating)

    def on_ask_ai_clicked(self):
        question = self.text_input.toPlainText().strip()
        if not question:
            QMessageBox.information(self, "Empty Question", "Please enter a question before clicking Ask AI.")
            return

        if self._ai_generating:
            return  # Ignore duplicate clicks

        self._start_ai_generation(question)

    def _start_ai_generation(self, question: str):
        self._ai_generating = True
        self._update_ask_ai_state()
        self.ai_status_label.setText("<b>AI:</b> Routing and analyzing locally...")
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
        self._update_ask_ai_state()

        if not result.success:
            self._show_ai_error(result.error or "Unknown error")
            return

        gen_s = result.inference_time_ms / 1000.0
        status_parts = [f"Analyzed with: {result.backend_used}"]
        status_parts.append(f"Route: {result.route_used.name}")
        status_parts.append(f"Time: {gen_s:.1f}s")
        
        self.ai_status_label.setText(f"<b>AI:</b> {' · '.join(status_parts)}")
        self.answer_text_edit.setPlainText(result.answer)

    def on_ai_error(self, error_msg: str):
        self._ai_generating = False
        self._update_ask_ai_state()
        self._show_ai_error(error_msg)

    def _show_ai_error(self, message: str):
        self.ai_status_label.setText("<b>AI:</b> Error")
        self.answer_text_edit.setPlainText(f"Could not generate answer:\n{message}")
        logger.error(f"AI error: {message}")
