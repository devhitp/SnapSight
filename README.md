# SnapSight

Privacy-first, on-device screen intelligence assistant designed for Windows PCs, with future optimization for Qualcomm Snapdragon AI PCs.

## Vision

SnapSight is a privacy-first, on-device screen intelligence assistant designed for Windows PCs, with future optimization for Qualcomm Snapdragon AI PCs.

## Current Status

Sprint 1 — Project Foundation

## Planned Architecture

Screen Capture → OCR/Vision → Context Builder → AI Router → Local LLM → Answer

## Development Setup

1. Clone repository
2. Create virtual environment: `python -m venv .venv`
3. Activate environment: `.venv\Scripts\activate`
4. Install dependencies: `pip install -r requirements.txt -r requirements-dev.txt`
5. Run application: `python -m app.main`
6. Run tests: `pytest`

## Current Limitations

- screen capture is not implemented yet
- OCR is not implemented yet
- local LLM is not implemented yet
- NPU acceleration is not implemented yet
