# SnapSight Performance Benchmarking (Sprint 8)

SnapSight includes a built-in benchmark harness to establish honest, reproducible performance baselines on whatever hardware the application runs on.

## Development Hardware

All measurements in this document were collected on:

| Property | Value |
|---|---|
| CPU | Intel Core i5-11400H @ 2.70 GHz |
| Cores | 6 cores / 12 threads |
| Architecture | AMD64 / x86-64 |
| RAM | ~7.7 GB available |
| GPU | None (no CUDA) |
| OS | Windows |
| OCR Backend | EasyOCR / PyTorch / CPU |
| LLM Backend | llama.cpp / CPU |
| Qualcomm NPU | **Not present — see Qualcomm section** |

## Running Benchmarks

```bash
# All benchmarks
python scripts/benchmark.py

# Individual sections
python scripts/benchmark.py --ocr         # OCR only
python scripts/benchmark.py --llm         # LLM only
python scripts/benchmark.py --router      # Router only
python scripts/benchmark.py --e2e         # End-to-end workflows only

# Machine-readable output (no private content in JSON)
python scripts/benchmark.py --json

# Legacy OCR shortcut (delegates to --ocr)
python scripts/benchmark_ocr.py
```

## Methodology

### Timing
- All latency measurements use `time.perf_counter()` — monotonic, high-resolution.
- Wall-clock time is never used for latency measurement.
- Each benchmark specifies:
  - **Warmup runs**: discarded, used to stabilize JIT / caches
  - **Measured runs**: the N runs whose timings produce stats

### Statistics
- **Min**: fastest run
- **Mean**: arithmetic average
- **Median**: 50th percentile
- **P95**: 95th percentile (nearest-rank) — represents the "slow tail"
- **Max**: slowest run

### Cold vs Warm
Cold and warm performance are always reported separately — they measure fundamentally different things:

| | Cold | Warm |
|---|---|---|
| **OCR** | First call including model/runtime init | Subsequent calls on pre-initialized backend |
| **LLM** | Model file loaded from disk + first generate | Subsequent generate() calls on in-memory model |

Never compare cold startup time directly against warm inference time.

### Memory
Memory is measured as process RSS (Resident Set Size) via `psutil` if available, falling back to Windows `GetProcessMemoryInfo`. RSS is the total memory footprint of the process as seen by the OS — it is **not** an exact breakdown of every underlying subsystem's allocation. GPU memory, if any, is not captured by RSS.

## OCR Benchmark

**Backend**: EasyOCR (PyTorch, CPU)  
**Input**: Synthetic blank images (no private screen content)  
**Date**: 2026-09-21 — Intel Core i5-11400H, AMD64, CPU-only

| Resolution | Warmup | Runs | Median | P95 |
|---|---|---|---|---|
| 800×600 | 1 | 5 | 1317 ms | 1347 ms |
| 1280×800 | 1 | 5 | 3225 ms | 3580 ms |
| 1920×1080 | 1 | 5 | 6046 ms | 6291 ms |

> **Note**: EasyOCR on CPU processes the entire image pipeline (preprocessing + neural inference) regardless of text density. Blank synthetic images represent pipeline overhead. Real screenshots with dense text may produce similar or longer latencies.

**Memory footprint after OCR init + inference**: ~456 MB RSS (includes PyTorch model weights).

## LLM Benchmark

**Backend**: llama.cpp / CPU  
**Model**: Phi-3.5-mini-instruct Q4_K_M (2.23 GB)  
**Date**: 2026-09-21 — Intel Core i5-11400H, AMD64, CPU-only

| Stage | Value |
|---|---|
| Model load (COLD) | 4864 ms |
| First inference (short question, COLD) | 20,656 ms |
| First inference (medium question, COLD) | 9,656 ms |
| Warm inference median (5 runs) | 9629 ms |
| Warm inference P95 | 10,703 ms |
| Tokens/sec (warm) | ~6.5 tok/s |
| Memory after load | ~2854 MB RSS |
| Memory after inference | ~2714 MB RSS |

> **Note**: The first inference is slower due to KV-cache warm-up. Subsequent calls on the same loaded model are faster (warm path). Tokens/sec may vary based on prompt length and `max_tokens` setting.

> **Model reuse**: The GGUF model is loaded **once** and kept in memory for the entire application session. Subsequent questions reuse the same `Llama` instance. This is verified by the model-reuse regression test in `tests/test_llm.py`.

## Router Benchmark

**Backend**: Deterministic keyword classifier (no neural network)

The router is sub-millisecond on all tested question types. It uses pure Python string matching and is negligible compared to OCR and LLM inference times. Exact values are displayed in the benchmark output with 3-decimal precision.

## End-to-End Benchmarks

| Workflow | Description |
|---|---|
| **Workflow B** | General question → router → LLM |
| **Workflow C** | Visual question → router → vision unavailable fallback |

Workflow A (Capture → OCR → LLM) requires a real screen capture and is not benchmarked in the automated script since it requires a live display.

## Memory Budget

Approximate RSS on the development machine:

| Stage | RSS |
|---|---|
| Application baseline | ~65 MB |
| After OCR init + inference | ~456 MB |
| After LLM load | measured at runtime |
| Combined OCR + LLM | typically 2.5–3.5 GB total |

> **Important**: The development machine has ~7.7 GB available RAM. Running EasyOCR and Phi-3.5-mini simultaneously is feasible but leaves limited headroom. On devices with ≤4 GB RAM, the LLM load may fail.

## Qualcomm Snapdragon NPU Benchmark

**Snapdragon NPU benchmark: NOT EXECUTED**

**Reason**: The development machine (Intel Core i5-11400H, AMD64) has no physical Snapdragon NPU. All measurements in this document are CPU-only results on Intel hardware.

Qualcomm AI Hub reference numbers for EasyOCR and Phi-3.5-mini are **external reference results** and are **not** SnapSight measurements. They must not be presented as SnapSight benchmark output.

NPU benchmarks must be collected on real Snapdragon hardware with the QNN execution provider initialized and verified.

## Interpreting Results

- **Median** is the most representative single-number summary for inference latency.
- **P95** tells you about slow-tail behavior — important for UX.
- **Mean** is influenced by outliers; use median for typical performance.
- OCR numbers on blank images are a lower bound on real-screen performance.
- LLM numbers depend heavily on prompt length and max_tokens setting.

## Privacy

The benchmark script collects only performance metadata:
- Hardware identity
- Timing measurements
- Memory RSS snapshots

It **never** captures, stores, or outputs:
- Screenshot pixel data
- OCR text content
- User question text
- Model prompt contents
- Any private screen content

JSON output (`--json`) contains only the above safe metadata.
