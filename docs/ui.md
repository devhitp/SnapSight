# SnapSight UI Architecture (Sprint 7)

SnapSight uses PySide6 (Qt) to provide a modern, professional desktop application experience. The design focuses on conveying privacy, localization, and simplicity.

## UX Flow
The user journey is heavily optimized for a three-step interaction:
1. **CAPTURE**: Take a snapshot of the screen (`Capture Window` or `Select Region`).
2. **ASK**: Ask an open-ended question about the snapshot ("What is the deadline here?") or a general question without needing a snapshot ("What is recursion?").
3. **ANSWER**: Receive a fully local inference result.

## Layout Hierarchy
The application adopts a **Card-Based Layout** built into `QSplitter` (two main horizontal columns) to present distinct logical areas:
- **Header**: Branding and high-level privacy promise (`🔒 On-device`).
- **Screen Context Card (Left Split)**: Encapsulates everything related to the visual input. Includes the capture preview and OCR processing states.
- **Ask AI Card (Top Right Split)**: The primary text input area for user prompts. Designed to be accessible directly via keyboard (`Ctrl+Enter`).
- **Answer Card (Bottom Right Split)**: The readonly output area, displaying the generated text and routing/backend telemetry.
- **Footer**: Granular, precise component hardware telemetry (e.g. `OCR: EasyOCR • CPU | LLM: llama.cpp • CPU`).

## State Management
SnapSight rigorously updates empty and loading states to keep the UI predictable:
- **Empty Preview**: Shows "Capture your screen to give SnapSight context" instead of a blank box.
- **Processing OCR**: "Reading screen..."
- **Processing AI**: "Thinking..." with the `Ask AI` button disabled to prevent concurrent/duplicate submissions.
- **Error States**: Rather than emitting tracebacks into the UI, specific errors (missing model, no visual backend, OCR failure) are caught and replaced with actionable, user-friendly instructions (e.g., "Local AI model not found. Place the required model in the models folder and try again.").

## Styling (`app/ui/styles.py`)
All UI components use a centralized Qt Stylesheet (`MODERN_DARK_THEME`). 
- Avoids repetitive `setStyleSheet` commands in the python code.
- Uses semantic classes (e.g., `QFrame.Card`, `QPushButton.Primary`) via `setProperty("class", "name")`.
- Modern, dark aesthetic inspired by VS Code and other professional productivity tools.
