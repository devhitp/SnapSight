# SnapSight

**Private, on-device screen intelligence assistant for Windows PCs with a Qualcomm Snapdragon-aware AI architecture.**

> **See your screen. Ask anything. Keep everything on-device.**

**Qualcomm Snapdragon AI Lab – Build & Present Challenge 2026**

**Project status: Development complete • Qualcomm AI Hub model validation complete**

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

### Sprint 6 — Qualcomm Snapdragon NPU Runtime & Validation
- **Hardware-Aware Runtime Detection** — detects platform, architecture, CPU vendor, and device information for hardware-specific execution paths.
- **Qualcomm OCR Runtime Path** — isolated `QualcommOCREngine` architecture prepared for `hrnet_w48_ocr.onnx` through ONNX Runtime + QNN Execution Provider.
- **Graceful CPU Fallback** — EasyOCR CPU remains the fallback when the Qualcomm runtime/model path is unavailable.
- **Qualcomm AI Hub Validation** — the official `HRNet-W48-OCR` model was successfully compiled, profiled, and inferred on a hosted Snapdragon X Elite CRD.
- **Verified NPU Execution** — Qualcomm AI Hub reported **all 820 model nodes executing on the Qualcomm Hexagon HTP v73 NPU**.
- **Measured Hosted-Device Results** — 1025.30 ms inference latency and 183.76 MB peak inference memory were recorded from SnapSight's submitted AI Hub jobs.

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
- **Separated Benchmarking** — local SnapSight CPU measurements and Qualcomm AI Hub hosted-device model validation are reported separately.

### Sprint 9 — Packaging, Deployment & Accessibility
- **Standalone Executable** — Packaged via PyInstaller into a distributable `dist/SnapSight` directory.
- **External Models** — Large model weights (`.gguf`, `.onnx`) strictly remain external to the packaged executable to keep the distribution size minimal.
- **Path Resolution** — Robust `app/utils/paths.py` securely resolves assets whether running from source or from the frozen PyInstaller `_MEIPASS`.
- **Missing Model UI** — No raw stack traces. The UI gracefully falls back and informs the user if a model is not correctly placed next to the executable.
- **Accessibility Enhancements** — Complete keyboard navigation with logical tab order, ARIA-style roles (`AccessibleName`), and visible focus outlines across all interactive UI controls.
- **Release Validation** — Automated script verifies that no secrets, `.env` files, models, or private captures leak into the release bundle.
- **Deployment Documentation** — For full packaging details, see [docs/deployment.md](docs/deployment.md).

### Sprint 10 — Final Demo, Documentation & Submission Readiness
- **Final Repository Audit** — source tree, release artifacts, secrets, and Git hygiene reviewed.
- **Documentation** — architecture, privacy, Qualcomm validation, performance, demo, and submission documentation finalized.
- **Qualcomm Evidence** — hosted Snapdragon X Elite CRD validation preserved with compile, profile, and inference job IDs.
- **Submission Readiness** — final pitch deck, PDF, project description, and demo materials prepared.
- **Security Review** — no API credentials, model weights, screenshots, or local machine secrets committed.

## Qualcomm AI Hub Validation

SnapSight's Qualcomm AI path was validated using the official `HRNet-W48-OCR` model through Qualcomm AI Hub's hosted Snapdragon hardware.

| Parameter | Verified Result |
|---|---|
| Target | Snapdragon X Elite CRD |
| OS | Windows 11 |
| Backend | Qualcomm Hexagon HTP v73 |
| Compute Unit | **NPU — all 820 nodes** |
| Compile | **SUCCESS** |
| Profile | **SUCCESS** |
| Inference | **SUCCESS** |
| Inference Latency | **1025.30 ms / frame** |
| Peak Inference Memory | **183.76 MB** |
| Input | `float32[1,3,1024,2048]` |
| Output | `float32[1,19,256,512]` |
| Compile Job | `jpxlx6n9p` |
| Profile Job | `jp2re90mg` |
| Inference Job | `j568wzz7g` |

> These are results from SnapSight's submitted Qualcomm AI Hub jobs for the standalone `HRNet-W48-OCR` model. They are not Qualcomm's published reference benchmarks and are not presented as full-application Snapdragon benchmarks.

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
# Place at: models/Phi-3.5-mini-instruct-Q4_K_M.gguf

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
| Expected path | `models/Phi-3.5-mini-instruct-Q4_K_M.gguf` |

Download from [Hugging Face — bartowski/Phi-3.5-mini-instruct-GGUF](https://huggingface.co/bartowski/Phi-3.5-mini-instruct-GGUF).

SnapSight will display a clear setup message if the model is missing. It **will not** download it automatically.

## Runtime Status

| Feature | Status |
|---|---|
| Screen Capture | ✅ Implemented |
| OCR (EasyOCR, CPU) | ✅ Implemented |
| Local LLM (llama.cpp, CPU) | ✅ Implemented |
| AI Router | ✅ Implemented (Deterministic intent classifier) |
| Vision Backend | ✅ Modular abstraction with unavailable fallback |
| Qualcomm OCR Runtime Path | ✅ Architecture prepared; model validated separately on Snapdragon via AI Hub |
| Qualcomm NPU Model Validation | ✅ **Verified on Snapdragon X Elite CRD** |

> **Qualcomm validation:** the standalone HRNet-W48-OCR model successfully executed on the Snapdragon X Elite CRD NPU through Qualcomm AI Hub, with all 820 model nodes reported on the NPU. The current SnapSight application code was not changed as part of this hosted-device validation.

## Current Limitations

- **Visual reasoning backend** — the modular vision interface exists, but a general-purpose local multimodal reasoning backend is not currently bundled.
- **Qualcomm OCR application integration** — the HRNet-W48-OCR model has been independently validated on Snapdragon X Elite NPU through Qualcomm AI Hub; the current `QualcommOCREngine` remains an architecture-ready integration path rather than a claimed end-to-end production text OCR implementation.
- **Local LLM model download** — Phi-3.5-mini requires the local GGUF model (~2.4 GB) to be placed in the expected model directory.
- **Voice input** — text input only.

## Performance

SnapSight includes a built-in benchmark harness for measuring real performance on the host hardware.

**Local SnapSight Benchmark Baseline**: x86-64 CPU execution on the development system.

**Qualcomm Hosted-Device Validation**: Snapdragon X Elite CRD NPU results are documented separately in the Qualcomm AI Hub Validation section.

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

## AI Architecture

```
Screen Capture
    ↓
OCR (EasyOCR CPU / Qualcomm-aware runtime path)
    ↓
AI Orchestrator (Router + Context Selector)
    ├── Local LLM (LlamaCpp)
    └── Vision Engine (Modular abstraction / fallback)
    ↓
Answer
```


## Project Links

- **GitHub:** https://github.com/devhitp/SnapSight
- **Qualcomm AI Hub model:** `HRNet-W48-OCR`
- **Challenge:** Qualcomm Snapdragon AI Lab – Build & Present Challenge 2026

## Final Status

SnapSight development is complete, the Windows desktop application has been packaged and audited, and the Qualcomm HRNet-W48-OCR model has been successfully validated on a hosted Snapdragon X Elite CRD NPU through Qualcomm AI Hub.
