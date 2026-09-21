"""
SnapSight Unified Benchmark Script (Sprint 8).

Measures real performance on the current hardware.
All measurements use time.perf_counter() (monotonic, high-resolution).

Usage:
    python scripts/benchmark.py              # run all benchmarks
    python scripts/benchmark.py --ocr        # OCR only
    python scripts/benchmark.py --llm        # LLM only
    python scripts/benchmark.py --router     # Router only
    python scripts/benchmark.py --e2e        # End-to-end workflows only
    python scripts/benchmark.py --json       # machine-readable JSON (no private content)

PRIVACY:
  JSON output contains only performance metadata and timing measurements.
  It NEVER contains: screenshot pixels, OCR text, user questions,
  model prompt contents, or any private screen data.

QUALCOMM NOTE:
  Snapdragon NPU benchmark is NOT EXECUTED on this machine.
  Reason: No physical Snapdragon NPU is present on the development hardware
  (Intel Core i5-11400H, AMD64). All measurements below are CPU-only.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import platform
import datetime

# Ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from app.utils.benchmark import (
    BenchmarkHarness,
    BenchmarkResult,
    make_result,
    _get_process_rss_mb,
)
from app.ai.ocr.runtime import detect_runtime
from app.ai.ocr.ocr_service import OCRService
from app.ai.router.router import QuestionRouter
from app.capture.models import CaptureResult, CaptureType
from app.ai.llm.llamacpp_engine import LlamaCppEngine

# Resolve model path from project root (where this script is run from)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BENCHMARK_MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "Phi-3.5-mini-instruct-Q4_K_M.gguf")


SEPARATOR = "-" * 60
SECTION = "=" * 60

# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_blank_image(width: int, height: int) -> QImage:
    """Create a synthetic blank white image (no private content)."""
    img = QImage(width, height, QImage.Format_RGB32)
    img.fill(0xFFFFFF)
    return img


def _make_capture(width: int = 1280, height: int = 800) -> CaptureResult:
    return CaptureResult(
        image=_make_blank_image(width, height),
        width=width,
        height=height,
        capture_type=CaptureType.FULLSCREEN,
    )


def _print_result(r: BenchmarkResult, extra_lines: list[str] | None = None):
    print(f"\nBenchmark : {r.name}")
    if r.backend:
        print(f"Backend   : {r.backend}")
    if r.accelerator:
        print(f"Accelerator: {r.accelerator}")
    if r.model:
        print(f"Model     : {r.model}")
    if r.input_description:
        print(f"Input     : {r.input_description}")
    print(f"Warmup    : {r.warmup_runs}  |  Measured: {r.measured_runs}")
    print(f"Success   : {r.success_count}  |  Failure: {r.failure_count}")
    if r.min_ms is not None:
        # Use 3 decimal places so sub-millisecond values (e.g. router) are visible
        fmt = ".3f" if r.min_ms is not None and r.min_ms < 1.0 else ".1f"
        print(f"Min       : {r.min_ms:{fmt}} ms")
        print(f"Mean      : {r.mean_ms:{fmt}} ms")
        print(f"Median    : {r.median_ms:{fmt}} ms")
        print(f"P95       : {r.p95_ms:{fmt}} ms")
        print(f"Max       : {r.max_ms:{fmt}} ms")
    if extra_lines:
        for line in extra_lines:
            print(line)
    print(SEPARATOR)


def _memory_snapshot(label: str):
    rss = _get_process_rss_mb()
    if rss is not None:
        print(f"  Memory ({label}): {rss:.1f} MB RSS")
    else:
        print(f"  Memory ({label}): unavailable")
    return rss


# ── OCR Benchmark ─────────────────────────────────────────────────────────────

def run_ocr_benchmark() -> list[BenchmarkResult]:
    print(f"\n{SECTION}")
    print("OCR BENCHMARK")
    print(SECTION)

    results = []

    print("\nInitializing OCR service...")
    init_start = time.perf_counter()
    try:
        service = OCRService()
    except Exception as e:
        print(f"OCR service initialization failed: {e}")
        return results
    init_ms = (time.perf_counter() - init_start) * 1000.0

    status = service._runtime_status
    backend_name = service._engine.engine_name if service.is_available else "Unavailable"
    accelerator = status.execution.accelerator.value

    print(f"Backend   : {backend_name}")
    print(f"Accelerator: {accelerator}")
    print(f"OCR Init  : {init_ms:.1f} ms (COLD — model + runtime init)")
    _memory_snapshot("after OCR init")

    if not service.is_available:
        print("OCR service unavailable — skipping inference benchmarks.")
        return results

    # Test resolutions (no private content — synthetic images)
    configs = [
        (1280, 800, "1280×800 (standard HD)"),
        (1920, 1080, "1920×1080 (full HD)"),
        (800, 600, "800×600 (small)"),
    ]

    for width, height, desc in configs:
        capture = _make_capture(width, height)

        r = make_result(
            f"OCR warm — {desc}",
            backend=backend_name,
            accelerator=accelerator,
            input_description=f"Synthetic blank image — {desc}",
            input_resolution=f"{width}x{height}",
        )

        harness = BenchmarkHarness(name=r.name, warmup=1, runs=5)

        def _run_ocr(cap=capture):
            service.process_capture(cap)
            return True

        harness.measure(_run_ocr, r)
        results.append(r)
        _print_result(r)

    _memory_snapshot("after OCR inference")
    return results


# ── Router Benchmark ──────────────────────────────────────────────────────────

def run_router_benchmark() -> list[BenchmarkResult]:
    print(f"\n{SECTION}")
    print("ROUTER BENCHMARK")
    print("(Deterministic keyword classifier — should be negligible vs inference)")
    print(SECTION)

    results = []
    router = QuestionRouter()

    test_cases = [
        ("What does it say?", "TEXT"),
        ("What color is the button?", "VISUAL"),
        ("What is recursion?", "GENERAL"),
        ("Explain this graph", "MIXED"),
        ("What error is shown?", "CODE"),
    ]

    for question, intent_name in test_cases:
        r = make_result(
            f"Router — {intent_name}",
            backend="QuestionRouter (deterministic)",
            accelerator="CPU",
            input_description=f"Question classified as {intent_name}",
        )
        harness = BenchmarkHarness(name=r.name, warmup=2, runs=20)

        def _route(q=question):
            router.route(q)
            return True

        harness.measure(_route, r)
        results.append(r)
        _print_result(r)

    return results


# ── LLM Benchmark ─────────────────────────────────────────────────────────────

def run_llm_benchmark() -> list[BenchmarkResult]:
    print(f"\n{SECTION}")
    print("LLM BENCHMARK")
    print(SECTION)

    results = []

    if not os.path.isfile(BENCHMARK_MODEL_PATH):
        print(f"\nLLM benchmark skipped — model file not found.")
        print(f"Expected: {BENCHMARK_MODEL_PATH}")
        print("See models/README.md for setup instructions.")
        return results

    print(f"\nModel found: {os.path.basename(BENCHMARK_MODEL_PATH)}")
    print(f"Model size: {os.path.getsize(BENCHMARK_MODEL_PATH) / (1024**3):.2f} GB")

    _memory_snapshot("before LLM load")

    # — Cold: model load —
    print("\nLoading model (COLD)...")
    load_start = time.perf_counter()
    engine = LlamaCppEngine(model_path=BENCHMARK_MODEL_PATH)
    # Trigger initialization explicitly
    load_result = engine._initialize()
    load_ms = (time.perf_counter() - load_start) * 1000.0

    if load_result is not None:
        print(f"LLM load FAILED: {load_result}")
        return results

    print(f"Model load (COLD): {load_ms:.1f} ms")
    _memory_snapshot("after LLM load")

    model_r = make_result(
        "LLM model load (COLD)",
        backend="llama.cpp",
        accelerator="CPU",
        model=engine.model_name,
        warmup_runs=0,
        measured_runs=1,
    )
    model_r.min_ms = model_r.max_ms = model_r.mean_ms = model_r.median_ms = model_r.p95_ms = load_ms
    model_r.success_count = 1
    results.append(model_r)

    # Verify model reuse
    _llm_before = id(engine._llm)

    # — Cold first inference —
    print("\nFirst inference (COLD — model already loaded, first generate() call)...")
    test_questions = [
        ("What is SnapSight?", "Short general question"),
        ("Explain what this application does in two sentences.", "Medium general question"),
    ]

    for question, desc in test_questions:
        first_r = make_result(
            f"LLM first inference — {desc}",
            backend="llama.cpp",
            accelerator="CPU",
            model=engine.model_name,
            input_description=desc,
        )
        harness = BenchmarkHarness(name=first_r.name, warmup=0, runs=1)

        def _gen_once(q=question):
            result = engine.generate(q, "")
            return result.success

        harness.measure(_gen_once, first_r)
        results.append(first_r)
        _print_result(first_r)

    # — Warm inference —
    print("\nWarm inference (model already loaded)...")
    warm_question = "What is SnapSight?"

    warm_r = make_result(
        "LLM warm inference",
        backend="llama.cpp",
        accelerator="CPU",
        model=engine.model_name,
        input_description="Short general question (repeated)",
    )
    harness = BenchmarkHarness(name=warm_r.name, warmup=1, runs=5)

    tokens_per_sec_list = []

    def _gen_warm(q=warm_question):
        result = engine.generate(q, "")
        if result.success and result.tokens_per_sec:
            tokens_per_sec_list.append(result.tokens_per_sec)
        return result.success

    harness.measure(_gen_warm, warm_r)
    results.append(warm_r)

    avg_tps = sum(tokens_per_sec_list) / len(tokens_per_sec_list) if tokens_per_sec_list else None
    extra = [f"Tokens/sec: {avg_tps:.2f}" if avg_tps else "Tokens/sec: unavailable"]
    _print_result(warm_r, extra)

    # — Model reuse verification —
    _llm_after = id(engine._llm)
    if _llm_before == _llm_after:
        print("Model reuse: VERIFIED — same model instance used for all generations.")
    else:
        print("Model reuse: WARNING — model instance changed between calls!")

    _memory_snapshot("after LLM inference")
    return results


# ── End-to-End Benchmarks ─────────────────────────────────────────────────────

def run_e2e_benchmark() -> list[BenchmarkResult]:
    print(f"\n{SECTION}")
    print("END-TO-END BENCHMARK")
    print(SECTION)

    results = []
    router = QuestionRouter()

    # Workflow B: General question (router + LLM)
    print("\nWorkflow B: General question (Router only, no OCR/capture)")
    t0 = time.perf_counter()
    decision = router.route("What is SnapSight?")
    route_ms = (time.perf_counter() - t0) * 1000.0

    b_r = make_result(
        "E2E Workflow B — General question routing",
        backend="QuestionRouter",
        accelerator="CPU",
        input_description="General question — no capture needed",
    )
    b_r.min_ms = b_r.max_ms = b_r.mean_ms = b_r.median_ms = b_r.p95_ms = route_ms
    b_r.measured_runs = 1
    b_r.success_count = 1
    b_r.notes = f"Route: {decision.intent.name}"
    results.append(b_r)
    _print_result(b_r, [f"Route: {decision.intent.name}"])

    # Workflow C: Visual question (router + vision unavailable fallback)
    print("\nWorkflow C: Visual question -> vision unavailable fallback")
    from app.ai.vision.unavailable_engine import UnavailableVisionEngine
    from app.ai.llm.llamacpp_engine import LlamaCppEngine as _LlamaCpp
    from app.ai.orchestrator import AIOrchestrator

    llm = _LlamaCpp()
    vision = UnavailableVisionEngine()
    orchestrator = AIOrchestrator(llm, vision)

    t0 = time.perf_counter()
    result = orchestrator.ask("What color is the button?", None, None)
    c_ms = (time.perf_counter() - t0) * 1000.0

    c_r = make_result(
        "E2E Workflow C — Visual question, unavailable fallback",
        backend="UnavailableVisionEngine (expected fallback)",
        accelerator="N/A",
        input_description="Visual question without capture",
    )
    c_r.min_ms = c_r.max_ms = c_r.mean_ms = c_r.median_ms = c_r.p95_ms = c_ms
    c_r.measured_runs = 1
    # Success here means it gracefully handled the unavailable state
    c_r.success_count = 1 if not result.success and result.error else 0
    c_r.notes = f"Vision engine gracefully declined: {result.error or 'no error'}"
    results.append(c_r)
    _print_result(c_r, [f"Fallback: {result.error or 'N/A'}"])

    return results


# ── Qualcomm Section ──────────────────────────────────────────────────────────

def print_qualcomm_status():
    print(f"\n{SECTION}")
    print("QUALCOMM / SNAPDRAGON NPU BENCHMARK")
    print(SECTION)
    print("\nSnapdragon NPU benchmark: NOT EXECUTED")
    print("Reason: No physical Snapdragon NPU is present on the development machine.")
    print(f"Current hardware: {platform.processor()}")
    print(f"Architecture: {platform.machine()}")
    print("\nQualcomm AI Hub reference results are NOT SnapSight measurements.")
    print("NPU benchmarks must be collected on real Snapdragon hardware.")
    print(SEPARATOR)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="SnapSight performance benchmark — Intel i5-11400H, CPU-only"
    )
    parser.add_argument("--ocr", action="store_true", help="Run OCR benchmark only")
    parser.add_argument("--llm", action="store_true", help="Run LLM benchmark only")
    parser.add_argument("--router", action="store_true", help="Run router benchmark only")
    parser.add_argument("--e2e", action="store_true", help="Run end-to-end benchmark only")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON (no private content)")
    args = parser.parse_args()

    run_all = not any([args.ocr, args.llm, args.router, args.e2e])

    # When --json: redirect all human-readable prints to stderr so stdout is pure JSON
    if args.json:
        sys.stdout = sys.stderr

    app = QApplication.instance() or QApplication(sys.argv)

    print(SECTION)
    print("SnapSight Development Benchmark")
    print(f"Hardware : {platform.processor()}")
    print(f"Arch     : {platform.machine()}")
    print(f"Platform : {platform.system()}")
    print(f"Date     : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(SECTION)

    _memory_snapshot("application baseline")

    all_results: list[BenchmarkResult] = []

    if run_all or args.ocr:
        all_results.extend(run_ocr_benchmark())

    if run_all or args.router:
        all_results.extend(run_router_benchmark())

    if run_all or args.llm:
        all_results.extend(run_llm_benchmark())

    if run_all or args.e2e:
        all_results.extend(run_e2e_benchmark())

    if run_all:
        print_qualcomm_status()

    if args.json:
        # JSON output — metadata only, NO private screen content
        # All human-readable text already went to stderr implicitly via the
        # benchmark functions, but print() goes to stdout. When --json is used,
        # we suppress the "Benchmark complete" footer and print only JSON so
        # the output is machine-parseable by piping stdout.
        # Restore real stdout and emit pure JSON
        sys.stdout = sys.__stdout__
        output = {
            "generated": datetime.datetime.now().isoformat(),
            "hardware": {
                "cpu": platform.processor(),
                "architecture": platform.machine(),
                "platform": platform.system(),
            },
            "qualcomm_npu": "NOT EXECUTED - No Snapdragon hardware available",
            "results": [r.to_dict() for r in all_results],
        }
        print(json.dumps(output, indent=2, default=str))
        return  # Exit cleanly

    print(f"\n{SECTION}")
    print(f"Benchmark complete. {len(all_results)} result(s) recorded.")
    print(SECTION)


if __name__ == "__main__":
    main()
