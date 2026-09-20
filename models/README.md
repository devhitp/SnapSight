# SnapSight Models Directory

This directory holds local AI model files. **No model files are committed to Git.**

## Required Model — Sprint 4 (Local LLM)

| Property | Value |
|---|---|
| **Model** | Phi-3.5-Mini-Instruct |
| **Quantization** | Q4_K_M (GGUF) |
| **File name** | `phi-3.5-mini-instruct.Q4_K_M.gguf` |
| **Expected path** | `models/phi-3.5-mini-instruct.Q4_K_M.gguf` |
| **Approx. size** | ~2.4 GB |
| **RAM requirement** | ~3–4 GB (plus ~2 GB for EasyOCR/PyTorch) |
| **Source** | [bartowski/Phi-3.5-mini-instruct-GGUF on Hugging Face](https://huggingface.co/bartowski/Phi-3.5-mini-instruct-GGUF) |

## Manual Download Instructions

1. Install [huggingface-cli](https://huggingface.co/docs/huggingface_hub/guides/cli) or download directly from the browser.
2. Download the Q4_K_M file:

```bash
huggingface-cli download bartowski/Phi-3.5-mini-instruct-GGUF \
  Phi-3.5-mini-instruct-Q4_K_M.gguf \
  --local-dir models/
```

3. Rename the file to match the expected path:
   `models/phi-3.5-mini-instruct.Q4_K_M.gguf`

4. Launch SnapSight:
```bash
python -m app.main
```

## Privacy

Model files run **100% locally**. No data is sent to any server during inference.

## Notes

- SnapSight will display a clear setup message if the model file is missing.
- EasyOCR models are stored separately (managed by the EasyOCR library).
- Do NOT commit `.gguf`, `.bin`, or `.safetensors` files.
