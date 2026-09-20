# SnapSight

Privacy-first, on-device screen intelligence assistant for Windows PCs, with future optimization for Qualcomm Snapdragon AI PCs.

> **See your screen. Ask anything. Keep everything on-device.**

## Current Status

Sprint 4 — Local AI Screen Q&A

## Pipeline

```
Screen Capture → OCR → Context Builder → Local LLM → Answer
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
- **Prompt-injection safety** — OCR text is treated as DATA, not instructions
- **Async generation** — UI remains responsive during inference
- **Model reuse** — model loaded once, reused for subsequent questions
- **CPU execution** — no GPU required

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
| Qualcomm ONNX/QNN backend | 🔲 Architecture prepared, not implemented |
| Verified Snapdragon NPU execution | ❌ Not yet — requires Snapdragon hardware + QNN integration |

> **Note on Qualcomm AI Hub:** Qualcomm AI Hub provides optimized ONNX/QNN profiles for both EasyOCR and Phi-3.5-mini on Snapdragon X Elite. These are **external reference profiles** and have not been integrated into SnapSight yet. Actual NPU performance must be measured on a Snapdragon device once the QNN backend is implemented.

## Current Limitations

- **No Snapdragon/NPU inference** — CPU only in development
- **No local LLM** without downloading the GGUF model (~2.4 GB)
- **No AI Router** — single local backend
- **No voice input** — text only

## Planned Architecture

```
Screen Capture
    ↓
OCR (EasyOCR)
    ↓
Context Builder
    ↓
LLM Router  ──┬── LocalCPU (LlamaCpp)
              └── Future: Qualcomm QNN
    ↓
Answer
```
