# SnapSight Demo Script

**Target Duration**: 2–4 Minutes
**Core Message**: "Ask Anything About Your Screen. Keep Everything On-Device."

## Pre-Flight Checklist
- Ensure the Windows desktop is clean (hide personal icons, close unrelated apps).
- Verify the `models/` directory contains `Phi-3.5-mini-instruct-Q4_K_M.gguf`.
- Open a safe application to capture (e.g., Wikipedia article about Snapdragon, or a generic block of code).

## Demo Flow

### 1. Introduction (0:00 - 0:30)
- **Action**: Launch `dist/SnapSight/SnapSight.exe`.
- **Narration**: "Welcome to SnapSight, a completely private screen intelligence assistant for Windows. The AI runs entirely on-device, meaning your screen data never goes to the cloud."
- **Action**: Point to the "🔒 On-device" indicator in the top right.

### 2. Screen Capture & OCR (0:30 - 1:00)
- **Action**: Bring up a sample webpage or document. Click **"✂️ Select Region"** in SnapSight.
- **Action**: Drag a box around a paragraph of text or code.
- **Narration**: "I can capture a specific region of my screen. SnapSight immediately extracts the text using its local visual pipeline."
- **Action**: Wait a few seconds for the UI to update to *Screen context ready*.

### 3. Screen Context Q&A (1:00 - 2:00)
- **Action**: In the "Ask AI" box, type: *"Summarize the text on my screen in one sentence."*
- **Action**: Press **Ctrl+Enter** (or click Ask AI).
- **Narration**: "Now I can ask the local LLM to analyze that screen context. Because we use a deterministic AI router, SnapSight intelligently routes the visual context to the LLM backend."
- **Action**: Wait for the answer to generate. 
- **Narration**: "And there is the answer, generated entirely locally without any internet connection."

### 4. General Q&A Routing (2:00 - 2:30)
- **Action**: Type a general question: *"What is a Neural Processing Unit?"*
- **Action**: Press **Ctrl+Enter**.
- **Narration**: "If I ask a general question, the AI Router recognizes that screen context is unnecessary. It bypasses the context builder, saving tokens, memory, and time."
- **Action**: Show the generation metadata in the UI (e.g., `Route: GENERAL`).

### 5. Snapdragon Architecture Readiness (2:30 - 3:00)
- **Action**: Point to the telemetry footer at the bottom of the window (`OCR: EasyOCR (CPU) | LLM: llama.cpp (CPU)`).
- **Narration**: "While I'm demonstrating this on an Intel CPU, SnapSight was built with a dynamic runtime architecture. It's prepared to detect Qualcomm Snapdragon hardware and seamlessly route OCR tasks to the NPU via ONNX and QNN, unlocking massive efficiency on AI PCs."
- **Action**: Close SnapSight.
- **Narration**: "Private screen intelligence, ready for the edge. Thank you."
