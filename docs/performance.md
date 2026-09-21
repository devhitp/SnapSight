# Performance & Benchmarks

SnapSight includes a built-in benchmark harness (`scripts/benchmark.py`) designed to transparently measure end-to-end latency and hardware execution profiles. 

## Benchmark Methodology
- **Granularity**: Measurements are taken using `time.perf_counter()` for monotonic high-resolution timing.
- **Cold vs Warm Execution**: The benchmark specifically isolates model loading (cold) from continuous interaction (warm). Large LLMs and PyTorch models cache layers and KV-states, which drastically changes latency profiles after the first query.
- **Metric Quality**: Captures minimum, mean, median, P95 (95th percentile worst-case), and maximum bounds over multiple iterations.
- **Memory Footprint**: Process RSS (Resident Set Size) is polled sequentially.

---

## Hardware Execution Baseline

> **Note:** The measurements below represent the reference CPU execution profile. SnapSight's runtime architecture natively supports hardware-specific execution paths (e.g., QNN) when supported environments are detected.

**Reference Benchmark Hardware:**
- **Architecture**: x86-64
- **OS**: Windows 11
- **Backend**: CPU (llama.cpp and PyTorch EasyOCR)

---

## Benchmark Results

### 1. Memory Profile
- **Application Baseline**: ~64 MB
- **After OCR Load**: ~368 MB
- **After LLM Load (Phi-3.5 2.4GB)**: ~2.38 GB
- **Peak AI Inference Footprint**: ~2.68 GB

*SnapSight comfortably operates within a 3 GB memory footprint, making it highly viable for edge AI PCs.*

### 2. OCR (Visual Signals Pipeline)
*Measured on a standard 1280x800 synthetic capture.*
- **Backend**: EasyOCR (CPU)
- **Median Latency**: 4,985 ms
- **P95 Latency**: 5,331 ms

### 3. LLM (Question & Answer Pipeline)
*Measured using Phi-3.5-mini-instruct-Q4_K_M.gguf.*
- **Backend**: llama.cpp (CPU)
- **Model Load Time (Cold)**: 7.22 seconds
- **First Inference (Cold)**: 46.30 seconds *(Includes initial context processing and KV-cache setup)*
- **Warm Inference (Subsequent Q&A)**: 8.59 seconds (Median)
- **Token Generation Speed**: 6.87 tokens/sec (CPU)

### 4. AI Orchestration & Routing
*Measures the deterministic intent router classifying user questions.*
- **Backend**: Regex/Heuristics
- **Latency**: 0.024 ms (Near-instantaneous, adding zero overhead to the workflow)
