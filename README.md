# SnapSight

Privacy-first, on-device screen intelligence assistant designed for Windows PCs, with future optimization for Qualcomm Snapdragon AI PCs.

## Vision

SnapSight is a privacy-first, on-device screen intelligence assistant designed for Windows PCs, with future optimization for Qualcomm Snapdragon AI PCs.

## Current Status

Sprint 2 — Screen Capture & Context Acquisition

## Planned Architecture

Screen Capture → OCR/Vision → Context Builder → AI Router → Local LLM → Answer

## Capture Capabilities (Sprint 2)

- **Window Capture**: Captures the active foreground window using native Windows APIs.
- **Region Selection**: Allows the user to select an arbitrary rectangular region of the screen.
- **Preview**: Displays the captured frame preserving aspect ratio.

## Development Setup

1. Clone repository
2. Create virtual environment: `python -m venv .venv`
3. Activate environment: `.venv\Scripts\activate`
4. Install dependencies: `pip install -r requirements.txt -r requirements-dev.txt`
5. Run application: `python -m app.main`
6. Run tests: `pytest`

## Current Limitations

- **OCR is NOT implemented yet.**
- **Local LLM is NOT implemented yet.**
- **AI routing is NOT implemented yet.**
- **NPU acceleration is NOT implemented yet.**
