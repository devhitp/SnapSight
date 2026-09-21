# Snapdragon NPU Architecture & Readiness

SnapSight is designed with the Qualcomm Snapdragon AI ecosystem in mind. While AI is notoriously resource-heavy, SnapSight's architecture prepares the pipeline for highly efficient Edge AI execution on Windows on Snapdragon (WoS) PCs.

## CURRENT DEVELOPMENT VERIFICATION: Intel CPU Only
> **IMPORTANT CAPABILITY DISCLOSURE:**
> The current physical development and verification of SnapSight was performed strictly on an **Intel Core i5 (x86-64)** Windows 11 machine. 
> 
> **NOT VERIFIED:**
> - Physical Snapdragon NPU execution
> - Snapdragon-specific performance improvements or benchmark results
> - NPU thermals or power draw
> 
> SnapSight's Qualcomm readiness is currently **Architecturally Prepared**, not physically verified. All benchmarks documented in this repository represent Intel CPU execution.

## Qualcomm Architecture

To allow seamless shifting from CPU to NPU execution without rewriting application logic, SnapSight implements a strict separation of Hardware Identity, Runtime Capability, and Actual Execution.

### 1. Hardware Detection
The `DeviceDetector` (`app/runtime/device_detector.py`) uses Windows-native mechanisms (via `wmi` or fallback `platform` metrics) to accurately detect the CPU Vendor and architecture. It avoids brittle assumptions (e.g., assuming all ARM64 is Snapdragon).

### 2. Runtime Capability Detection
The `RuntimeDetector` evaluates whether the host environment can actually load the required drivers. It probes for the presence of the `QNNExecutionProvider` in ONNX Runtime without crashing if it's missing.

### 3. Qualcomm OCR Abstraction
If Snapdragon hardware and the QNN execution provider are present, SnapSight automatically routes OCR inference to the `QualcommOCREngine` (`app/ai/ocr/qualcomm_engine.py`). 
- This engine is architecturally designed to ingest the `hrnet_w48_ocr.onnx` model (available via the Qualcomm AI Hub).
- If QNN fails to initialize, or the ONNX model is missing, the engine gracefully falls back to the CPU-based `EasyOCREngine` seamlessly.

### 4. Component-Level Runtime Status
The application telemetry (visible in the footer and JSON benchmark output) accurately isolates runtime backend status. It explicitly states whether OCR is executing via `EasyOCR (CPU)` or `Qualcomm (NPU)`. 

This transparent architecture ensures that when SnapSight is deployed to physical Snapdragon hardware in the future, NPU acceleration can be verified natively without codebase overhauls.
