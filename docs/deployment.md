# Deployment & Packaging Guide

This document describes the Windows packaging architecture for SnapSight.

## Environment Requirements
**Reference Baseline Execution**:
- Architecture: x86-64 (Windows 11)
- Backends: CPU (EasyOCR / `llama.cpp`)
- Validation: Packaged executable launch with bundled dependencies

**Hardware-Specific Execution**:
- Runtime paths (e.g., QNN/NPU) are architecturally supported via dynamic runtime selection.
- Hardware-specific performance and execution are selectively enabled when the target environment (e.g., Windows on Snapdragon) is detected.

## Packaging SnapSight (PyInstaller)

SnapSight uses PyInstaller to bundle its Python environment into a self-contained executable.

### Build Instructions

1. Ensure your virtual environment is active.
2. Install PyInstaller:
   ```cmd
   pip install pyinstaller
   ```
3. Run the automated build script:
   ```cmd
   python scripts/build_windows.py
   ```
4. The packaged application will be generated at `dist/SnapSight/SnapSight.exe`.

### Packaging Architecture

The build is configured as a `onedir` distribution rather than `onefile`. 
A single directory provides significantly faster application startup, which is critical for a desktop utility.

## Model Provisioning (IMPORTANT)

**Large model weights (.gguf, .onnx) are intentionally excluded from the executable bundle.** Bundling these would create an unmanageably large package and make model updates impossible without recompilation.

To use the packaged executable, you **must** provision the models manually alongside the executable.

1. Navigate to the `dist/SnapSight/` directory.
2. Create a `models/` directory next to `SnapSight.exe`.
3. Place your model files into this folder.

Expected file structure:
```
dist/
└── SnapSight/
    ├── SnapSight.exe
    ├── _internal/
    └── models/
        ├── Phi-3.5-mini-instruct-Q4_K_M.gguf  (approx 2.4 GB)
        └── [other optional ONNX models if using Qualcomm backend]
```

### Missing Model Behavior
If a required model is missing:
- **LLM Models**: The application will *not* crash. The AI Answer box will gracefully display a message explaining that the model is missing, while Screen Capture and OCR remain fully functional.
- **OCR Models**: If EasyOCR downloads are incomplete, OCR will fail safely, emitting a user-friendly error in the UI.

SnapSight **never** automatically downloads multi-GB models and **never** falls back to cloud APIs.

## Privacy & Security

- **No Telemetry**: SnapSight does not bundle crash reporters or analytics.
- **Local Only**: All Screen OCR and LLM inference occur strictly on-device.
- **Release Validation**: The build process ensures that sensitive files like `.env`, API keys, test screenshots, and logs are stripped from the distribution.

## Accessibility

The SnapSight UI has been built with native accessibility in mind:
- **Keyboard Navigation**: Logical tab order (Capture → Region → Question → AI).
- **Shortcuts**: `Ctrl+Enter` triggers AI generation. `Escape` cancels region selection.
- **Screen Readers**: Elements use `AccessibleName` and `AccessibleDescription` properties.
- **Visual Focus**: Distinct blue focus outlines appear when navigating interactive elements via keyboard.
- **Scaling**: Controls use expanding layouts, remaining robust at 125% and 150% Windows display scaling.
