# Submission Material: SnapSight

**Project Name**: SnapSight
**Tagline**: See your screen. Ask anything. Keep everything on-device.

## Problem
In modern computing workflows, users constantly need to synthesize, summarize, and question the information on their screen. However, current AI screen-reading solutions typically upload captures to the cloud. This introduces severe privacy risks (exposing banking data, internal code, and private messages to third-party endpoints) and introduces network latency. 

## Solution
SnapSight is a completely local, privacy-first desktop AI assistant. It allows users to capture a region of their screen and immediately ask natural language questions about it. The entire pipeline—from pixel capture to text extraction (OCR) to LLM generative answers—executes 100% on-device.

## Key Innovation
SnapSight features a deterministic **AI Router** and **Context Builder**. Rather than blindly injecting screen pixels into massive vision models, SnapSight extracts semantic text blocks and intelligently routes the user's prompt. If a user asks a general question, the system skips injecting screen context altogether. This dynamic orchestration saves gigabytes of memory and drastically reduces time-to-first-token compared to monolithic vision models.

## Local AI Architecture
1. **Screen Capture**: Native Windows API boundary capture.
2. **OCR**: Local PyTorch execution extracting bounding boxes and text.
3. **Context Builder**: Transforms bounding boxes into LLM-safe semantic chunks, strictly separated from prompt instructions to prevent prompt injection.
4. **Local LLM**: Powered by `llama.cpp` and GGUF quantization (e.g., Phi-3.5-mini), allowing state-of-the-art inference within a 3GB memory footprint.

## Snapdragon Readiness (Architecture)
SnapSight is architecturally built to leverage Windows on Snapdragon (WoS) AI PCs. It implements a strict separation of Hardware Identity and Runtime Capability. If Snapdragon hardware and the QNN Execution Provider are detected, SnapSight seamlessly shifts OCR workloads to an isolated `QualcommOCREngine` (ingesting `hrnet_w48_ocr.onnx`). *Note: The runtime architecture automatically selects the most efficient execution path (CPU, GPU, or NPU) depending on the detected hardware environment.*

## Privacy Model
- **No Telemetry**: No user analytics or crash reports.
- **Zero Cloud APIs**: No data is sent to OpenAI, Anthropic, Gemini, or remote vision APIs.
- **Edge Security**: Screen captures are held entirely in volatile RAM and never written to disk during production execution.

## Deployment & Accessibility
SnapSight is packaged as a standalone Windows executable via PyInstaller. To minimize distribution bloat, heavy multi-gigabyte models remain external and are provisioned locally. The UI is built with PySide6, featuring complete keyboard navigability (ARIA-style roles, visible focus outlines, and logical tab orders) and high-DPI scaling robustness.
