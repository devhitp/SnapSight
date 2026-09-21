# Privacy & Data Security

SnapSight was designed from day one around a single, foundational principle: **Keep everything on-device.**

By leveraging local LLMs and OCR frameworks, SnapSight offers robust screen intelligence without sacrificing user privacy or exposing sensitive desktop information to third parties.

## Application-Level AI Privacy Behavior

### 1. Screen Data Stays Local
When SnapSight captures the active window or a selected screen region, the image data (`CaptureResult`) is held entirely in local RAM. It is never saved to the disk (outside of testing contexts) and is never transmitted over a network.

### 2. OCR Runs Locally
The text extracted from your screen by the OCR framework (EasyOCR or Qualcomm OCR) is processed directly on your local CPU or NPU. No OCR text is sent to cloud-based vision APIs (like Google Cloud Vision or AWS Rekognition).

### 3. LLM Runs Locally
SnapSight's Q&A capabilities are powered by a locally loaded `.gguf` model (e.g., Phi-3.5) running via `llama.cpp`. 
- No OpenAI (ChatGPT)
- No Anthropic (Claude)
- No Gemini
- No remote AI endpoints

Your questions, the context extracted from your screen, and the AI's generated responses are strictly contained within your machine's memory boundaries.

### 4. No Telemetry or Accounts
SnapSight does not require a user account, login, or subscription. There are no analytics trackers, crash reporting services, or telemetry modules silently phoning home. The application does not collect usage patterns or query logs.

### 5. Independent Model Provisioning
The external AI model files required to run SnapSight remain locally controlled. The application does not automatically fetch massive, opaque model weights from the internet upon launch.

---

*(Note: While SnapSight contains no application-level AI network dependencies, underlying operating system behaviors, PySide6 framework initialization, or environment management tools (like pip/Python) may perform standard network operations unrelated to SnapSight's core privacy guarantees.)*
