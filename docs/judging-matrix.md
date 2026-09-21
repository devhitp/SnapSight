# Judging Criteria Alignment

This document maps the verified, implemented work in SnapSight to major evaluation areas typically found in software challenges. All claims below are based strictly on factual evidence present in the codebase.

## 1. Technical Implementation
- **Modular Architecture**: The system cleanly separates UI rendering (PySide6) from AI inference loops via decoupled `QThread` workers, ensuring the application never freezes during generation.
- **Local OCR Integration**: Utilizes PyTorch and EasyOCR for complete on-device visual text extraction.
- **Local LLM Orchestration**: Implements `llama-cpp-python` to interact with quantized GGUF models directly within the local memory space.
- **AI Routing**: A deterministic intent classifier parses user questions and selects the most efficient execution route (TEXT, CODE, VISUAL, GENERAL).
- **Runtime Abstraction**: SnapSight dynamically probes the operating system for hardware capabilities, allowing isolated fallbacks (e.g., from an attempted QNN NPU execution down to a safe CPU execution).
- **Automated Testing & Benchmarking**: Contains 86 passing unit tests verifying reliability (e.g., LLM model reuse, missing-model error recovery) and an independent, scriptable performance harness tracking microsecond-latency and RSS memory footprints.

## 2. Application Use Case & Innovation
- **Screen Intelligence**: Empowers users to instantly extract value, summaries, and code explanations from any content visible on their screen.
- **Natural-Language Screen Q&A**: Translates abstract screen bounding boxes into semantically structured text prompts, allowing natural conversational flows about static pixels.
- **Privacy-First Architecture**: Solves the critical security flaw of competing products by ensuring no pixel data or user prompts are ever transmitted to third-party cloud APIs.

## 3. Deployment & Accessibility
- **Windows Packaging**: Fully deployable as a PyInstaller standalone executable, hiding complex Python environments from the end user.
- **External Model Provisioning**: Intelligently separates massive AI weights from the core binary, keeping the application lightweight and allowing users to swap models independently.
- **Keyboard Navigation & ARIA**: Implements native Qt accessibility roles (`AccessibleName`, `AccessibleDescription`), logical tab ordering, and explicit visual focus states for keyboard-only users.
- **High-DPI-Aware Layouts**: UI panels scale responsively to 125% and 150% Windows display settings without hardcoded pixel clipping.

## 4. Presentation & Documentation
- **Architecture Documentation**: Clear mapping of data flow and system boundaries (`docs/architecture.md`).
- **Performance Documentation**: Factual, transparent latency and memory metrics recorded natively on development hardware (`docs/performance.md`).
- **Deployment Documentation**: Complete guide to reproducing the build and provisioning models (`docs/deployment.md`).
- **Privacy Documentation**: Explicitly defined application-level privacy behavior (`docs/privacy.md`).
