# SnapSight

Privacy-first, on-device screen intelligence assistant designed for Windows PCs, with future optimization for Qualcomm Snapdragon AI PCs.

## Vision

SnapSight is a privacy-first, on-device screen intelligence assistant designed for Windows PCs, with future optimization for Qualcomm Snapdragon AI PCs.

## Current Status

Sprint 3 — OCR & Screen Text Understanding

## Planned Architecture

Screen Capture → OCR/Vision → Context Builder → AI Router → Local LLM → Answer

## Capture Capabilities (Sprint 2)

- **Window Capture**: Captures the active foreground window using native Windows APIs.
- **Region Selection**: Allows the user to select an arbitrary rectangular region of the screen.
- **Preview**: Displays the captured frame preserving aspect ratio.

## OCR Capabilities (Sprint 3)

- **Local OCR**: Extracts structured text and bounding boxes from the captured image.
- **EasyOCR Integration**: Uses a local EasyOCR backend powered by PyTorch for robust offline processing.
- **Privacy-First**: No cloud OCR APIs, no telemetry, and no screenshot uploads. Everything runs completely locally.
- **Runtime Detection**: Features an isolated engine architecture and dynamic runtime detection. It currently uses CPU fallback.
- **Future Architecture**: Architecturally prepared to support Qualcomm ONNX Runtime + QNN acceleration when verifying supported hardware in future iterations.

## Development Setup

1. Clone repository
2. Create virtual environment: `python -m venv .venv`
3. Activate environment: `.venv\Scripts\activate`
4. Install base dependencies: `pip install -r requirements.txt -r requirements-dev.txt`
5. Install optional OCR dependencies (Warning: installs PyTorch): `pip install -r requirements-ocr.txt`
6. Run application: `python -m app.main`
7. Run tests: `pytest`

## Current Limitations

- **Verified NPU OCR Execution is NOT implemented yet.** (SnapSight provides a runtime path for ONNX Runtime/QNN acceleration, but currently uses CPU).
- **Local LLM is NOT implemented yet.**
- **AI routing is NOT implemented yet.**
