# SnapSight

Privacy-first, on-device screen intelligence assistant for Windows PCs, with future optimization for Qualcomm Snapdragon AI PCs.

> **See your screen. Ask anything. Keep everything on-device.**

Sprint 9 — Packaging, Deployment & Accessibility

## Pipeline

```
Screen Capture → OCR + Vision Engines
                  ↓
User Question → AI Router → Context Selector
                  ↓
          Local AI Orchestrator
                  ↓
   Local LLM or Local Vision Backend
                  ↓
               Answer
```

## Capabilities

### Sprint 2 — Screen Capture
- Window capture (native Windows APIs via ctypes)
- Interactive region selection overlay
- Multi-monitor support

### Sprint 3 — OCR
- Local EasyOCR integration (PyTorch/CPU)
- Structured OCR results with bounding boxes
- Async processing (UI stays responsive)

### Sprint 4 — Local AI
- **Local LLM** using [Phi-3.5-Mini-Instruct](https://huggingface.co/bartowski/Phi-3.5-mini-instruct-GGUF) via llama-cpp-python
- **Screen context Q&A** — ask natural language questions about captured screen content
- **ContextBuilder** — converts OCR results into safe, LLM-ready prompts
- **CPU execution** — no GPU required

### Sprint 5 — AI Router & Multimodal Vision
- **Intelligent Routing** — deterministic intent classifier routing questions to TEXT, CODE, VISUAL, MIXED, or GENERAL routes.
- **Context Selection** — orchestrator provides only the necessary context (e.g., skips sending OCR context for general/visual questions) to save tokens and time.
- **Vision Abstraction** — clean `VisionEngine` interface prepared for multimodal understanding.
- **Unavailable Fallback** — cleanly handles visual queries by explaining that no vision backend is currently installed.

### Sprint 6 — Qualcomm Snapdragon NPU Runtime & Optimization
- **Hardware-Aware Runtime Detection** — reliably detects platform, architecture, CPU vendor (Intel/AMD/Qualcomm) and device using Windows specific queries.
- **Qualcomm OCR Backend** — isolated `QualcommOCREngine` architecturally ready to load `hrnet_w48_ocr.onnx` via ONNX Runtime + QNN Execution Provider.
- **Graceful CPU Fallback** — explicitly falls back to EasyOCR if QNN cannot initialize or the model is missing, ensuring Intel/x86 dev environments continue to function seamlessly.
- **Factual Benchmarking** — independent OCR benchmark tool providing transparent, verifiable latency metrics and hardware tracking without faking NPU status.

### Sprint 7 — Product Polish + UX
- **Modern Dark Theme** — unified UI styling using Qt stylesheets for a professional, trustworthy desktop application aesthetic.
- **Card-Based Layout** — strict visual hierarchy separating *Screen Context*, *Ask AI*, and *Answer* into distinct cards.
- **Improved Empty States & Error Handling** — user-friendly messages for missing models or failed OCR instead of raw stack traces.
- **Keyboard Shortcuts** — added `Ctrl+Enter` to quickly submit questions and `Escape` to gracefully exit the region selector.
- **Granular Telemetry Footer** — decoupled runtime hardware status into a compact, unobtrusive footer.

### Sprint 8 — Performance, Benchmarking & Reliability
- **Benchmark Harness** — typed `BenchmarkResult` + `BenchmarkHarness` with warmup, min/mean/median/p95/max using `time.perf_counter()`.
- **Unified Benchmark Script** — `python scripts/benchmark.py [--ocr|--llm|--router|--e2e|--json]` for reproducible measurements.
- **Cold/Warm Separation** — model initialization and inference benchmarked independently.
- **Model Reuse Verified** — regression test confirms the GGUF is loaded once and reused across all questions.
- **Memory Measurement** — process RSS tracked via `psutil` at each pipeline stage.
- **Reliability Tests** — repeated-operation, error-recovery, and worker lifecycle tests.
- **Honest Qualcomm Section** — benchmark explicitly states NPU results not executed on development hardware.

### Sprint 9 — Packaging, Deployment & Accessibility
- **Standalone Executable** — Packaged via PyInstaller into a distributable `dist/SnapSight` directory.
- **External Models** — Large model weights (`.gguf`, `.onnx`) strictly remain external to the packaged executable to keep the distribution size minimal.
- **Path Resolution** — Robust `app/utils/paths.py` securely resolves assets whether running from source or from the frozen PyInstaller `_MEIPASS`.
- **Missing Model UI** — No raw stack traces. The UI gracefully falls back and informs the user if a model is not correctly placed next to the executable.
- **Accessibility Enhancements** — Complete keyboard navigation with logical tab order, ARIA-style roles (`AccessibleName`), and visible focus outlines across all interactive UI controls.
- **Release Validation** — Automated script verifies that no secrets, `.env` files, models, or private captures leak into the release bundle.
- **Deployment Documentation** — For full packaging details, see [docs/deployment.md](docs/deployment.md).

## Privacy & Local Execution

SnapSight processes everything **100% on-device**:
- No screenshots uploaded
- No OCR text sent to cloud
- No questions or answers transmitted externally
- No telemetry or analytics
- No internet connection required during inference

## Development Setup

```bash
# 1. Clone and create virtual environment
python -m venv .venv
.venv\Scripts\activate

# 2. Base dependencies
pip install -r requirements.txt -r requirements-dev.txt

# 3. OCR dependencies (installs PyTorch ~2 GB)
pip install -r requirements-ocr.txt

# 4. LLM dependencies
pip install -r requirements-llm.txt

# 5. Download the local LLM model (~2.4 GB) — see models/README.md
# Place at: models/phi-3.5-mini-instruct.Q4_K_M.gguf

# 6. Run
python -m app.main

# 7. Tests (no model required)
pytest
```

## Model Setup (Sprint 4)

| Property | Value |
|---|---|
| Model | Phi-3.5-Mini-Instruct |
| Quantization | Q4_K_M (GGUF) |
| Runtime | llama-cpp-python |
| Size | ~2.4 GB |
| RAM needed | ~3–4 GB (+ ~2 GB for EasyOCR) |
| Expected path | `models/phi-3.5-mini-instruct.Q4_K_M.gguf` |

Download from [Hugging Face — bartowski/Phi-3.5-mini-instruct-GGUF](https://huggingface.co/bartowski/Phi-3.5-mini-instruct-GGUF).

SnapSight will display a clear setup message if the model is missing. It **will not** download it automatically.

## Runtime Status

| Feature | Status |
|---|---|
| Screen Capture | ✅ Implemented |
| OCR (EasyOCR, CPU) | ✅ Implemented |
| Local LLM (llama.cpp, CPU) | ✅ Implemented |
| AI Router | ✅ Implemented (Deterministic intent classifier) |
| Vision Backend | 🔲 Architecture prepared, fallback unavailable state |
| Qualcomm ONNX/QNN backend | 🔲 Architecture prepared, gracefully falls back to CPU |
| Qualcomm/QNN hardware acceleration | 🔲 Architecture prepared for Snapdragon Windows PCs |

> **Note:** The current performance measurements represent the CPU execution profile. The runtime architecture natively supports hardware-specific execution paths (e.g., QNN) when supported environments are detected.

## Current Limitations

- **No local vision backend** — visual questions will trigger a fallback message since no local multi-modal model is installed on the current environment.
- **Reference CPU benchmark profile** — Baseline measurements reflect CPU execution.
- **No local LLM** without downloading the GGUF model (~2.4 GB)
- **No voice input** — text only

## Performance

SnapSight includes a built-in benchmark harness for measuring real performance on the host hardware.

**Reference Benchmark Hardware**: x86-64, CPU-only (baseline execution)

```bash
python scripts/benchmark.py           # all benchmarks
python scripts/benchmark.py --ocr     # OCR
python scripts/benchmark.py --llm     # LLM
python scripts/benchmark.py --router  # Router
python scripts/benchmark.py --e2e     # End-to-end
python scripts/benchmark.py --json    # Machine-readable (no private content)
```

**Keyboard shortcuts**: `Ctrl+Enter` submits the AI question.

See [`docs/performance.md`](docs/performance.md) for full methodology, cold/warm distinction, and memory measurement approach.

## Planned Architecture

```
Screen Capture
    ↓
OCR (EasyOCR / Qualcomm QNN fallback)
    ↓
AI Orchestrator (Router + Context Selector)
    ├── Local LLM (LlamaCpp)
    └── Vision Engine (Currently Unavailable Fallback)
    ↓
Answer
```
