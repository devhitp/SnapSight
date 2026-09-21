# System Architecture

SnapSight is designed as a modular, local-first intelligence pipeline. The architecture guarantees that no screen data leaves the device while providing an abstracted backend system that can dynamically switch between CPU, GPU, and NPU execution.

## Data Flow Pipeline

```text
1. Capture        : Windows Desktop → Pixels
        ↓
2. Vision/OCR     : Pixels → Bounding Boxes & Text (OCRService)
        ↓
3. Context Builder: OCR Data → Spatial/Semantic Text Block
        ↓
4. Question Router: User Prompt → Intent Classification (TEXT, CODE, VISUAL)
        ↓
5. Orchestrator   : Router Intent + Context + User Prompt → Final LLM Prompt
        ↓
6. AI Backend     : Final LLM Prompt → Local Generative AI (LLMEngine)
        ↓
7. Answer         : AI Output → PyQt Desktop UI
```

## Core Components

### 1. Capture Subsystem (Implemented & Verified)
Uses native Windows APIs (via `ctypes` and `QScreen`) to capture pixel data from the active window or user-defined regions without requiring heavy generic libraries. 

### 2. OCR Abstraction (Implemented & Verified)
The `OCRService` provides an interface to extract text. It abstracts the underlying inference engine:
- **EasyOCR (CPU/GPU)**: The default implementation utilizing PyTorch.
- **Qualcomm OCR (Architecturally Prepared)**: An isolated QNN execution path ready to process `hrnet_w48_ocr.onnx` models if a supported Snapdragon NPU is detected.

### 3. Context Builder (Implemented & Verified)
Transforms raw OCR bounding boxes into LLM-digestible text. It reconstructs reading order and strictly separates prompt instructions from raw data using text boundaries to prevent prompt injection attacks.

### 4. Question Router (Implemented & Verified)
To save AI tokens and processing time, a deterministic heuristic router classifies the user's intent. If a user asks a general question ("What is the capital of France?"), the orchestrator skips injecting the massive OCR text chunk, saving gigabytes of memory and seconds of latency.

### 5. LLM Abstraction (Implemented & Verified)
The `LLMEngine` defines the local AI generation contract. 
- **LlamaCppEngine (Implemented & Verified)**: Utilizes `llama-cpp-python` to interact with `GGUF` format models (e.g., Phi-3.5) entirely on the CPU.
- *Future expansions can seamlessly inject a Qualcomm-native LLM engine here.*

### 6. UI Worker Thread Architecture (Implemented & Verified)
AI processes are highly compute-intensive. SnapSight utilizes PySide6 `QThread` components (`AIWorker`, `OCRWorker`) to completely decouple AI inference from the main UI thread. This ensures the application remains responsive, cancelable, and smooth during the 40+ seconds of cold AI inference.

## Privacy Boundaries
SnapSight enforces a hard boundary at the edge. The system contains exactly **zero** cloud dependencies. Network access is not required at runtime. Context, OCR, and AI generation are executed strictly within the local memory bounds of the Windows executable.
