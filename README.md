# SnapSight

Privacy-first, on-device screen intelligence assistant for Windows PCs, with future optimization for Qualcomm Snapdragon AI PCs.

> **See your screen. Ask anything. Keep everything on-device.**

Sprint 7 — Product Polish + UX

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
| Verified Snapdragon NPU execution | ❌ Not yet — requires Snapdragon hardware + model artifact |

> **Note on Qualcomm AI Hub:** Qualcomm AI Hub provides optimized ONNX/QNN profiles for both EasyOCR and Phi-3.5-mini on Snapdragon X Elite. These are **external reference results** and have not been integrated into SnapSight yet. Actual NPU performance must be measured on a real Snapdragon device. SnapSight benchmarks will strictly reflect the hardware they are run on.

## Current Limitations

- **No local vision backend** — visual questions will trigger a fallback message since no local multi-modal model is installed on the current environment.
- **No Snapdragon/NPU inference** — CPU only in development
- **No local LLM** without downloading the GGUF model (~2.4 GB)
- **No voice input** — text only

## Planned Architecture

```
Screen Capture
    ↓
OCR (EasyOCR)
    ↓
AI Orchestrator (Router + Context Selector)
    ├── Local LLM (LlamaCpp)
    └── Vision Engine (Currently Unavailable Fallback)
    ↓
Answer
```
