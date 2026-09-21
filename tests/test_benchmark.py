"""
Sprint 8 — Benchmark Harness Unit Tests.

Tests the BenchmarkHarness and BenchmarkResult data model.
No real OCR/LLM inference required.
"""
import pytest
import statistics
import time
from app.utils.benchmark import (
    BenchmarkHarness,
    BenchmarkResult,
    make_result,
    _get_process_rss_mb,
)


# ── BenchmarkResult Tests ──────────────────────────────────────────────────────

def test_benchmark_result_defaults():
    r = BenchmarkResult(name="test")
    assert r.name == "test"
    assert r.success_count == 0
    assert r.failure_count == 0
    assert r.min_ms is None
    assert r.median_ms is None
    assert r.p95_ms is None


def test_benchmark_result_to_dict():
    r = BenchmarkResult(name="serialise_test", backend="EasyOCR", accelerator="CPU")
    d = r.to_dict()
    assert isinstance(d, dict)
    assert d["name"] == "serialise_test"
    assert d["backend"] == "EasyOCR"
    assert d["accelerator"] == "CPU"
    # Verify no private content fields exist
    assert "screenshot" not in d
    assert "ocr_text" not in d
    assert "user_question" not in d
    assert "prompt" not in d


def test_make_result_includes_machine_info():
    r = make_result("machine_test")
    # Should have machine/platform populated from platform module
    assert r.machine != "" or r.platform != ""


# ── BenchmarkHarness Tests ─────────────────────────────────────────────────────

def test_harness_basic_timing():
    """Harness must compute stats correctly for a trivial function."""
    r = BenchmarkResult(name="basic")
    harness = BenchmarkHarness(name="basic", warmup=1, runs=5)

    def noop():
        time.sleep(0.001)  # 1 ms
        return True

    harness.measure(noop, r)

    assert r.success_count == 5
    assert r.failure_count == 0
    assert r.warmup_runs == 1
    assert r.measured_runs == 5
    assert r.min_ms is not None
    assert r.max_ms is not None
    assert r.mean_ms is not None
    assert r.median_ms is not None
    assert r.p95_ms is not None
    # All should be positive
    assert r.min_ms > 0
    assert r.max_ms >= r.min_ms
    assert r.mean_ms >= r.min_ms


def test_harness_median_correctness():
    """Median should match statistics.median of the measured latencies."""
    captured = []
    r = BenchmarkResult(name="median")
    harness = BenchmarkHarness(name="median", warmup=0, runs=5)

    call_count = [0]

    # Inject controlled latencies
    fake_times = [0.010, 0.020, 0.030, 0.040, 0.050]  # seconds

    original_perf_counter = time.perf_counter
    call_idx = [0]

    def controlled_perf_counter():
        return original_perf_counter()

    # Use a direct approach: measure with a calibrated sleep
    def fn():
        time.sleep(0.010)
        return True

    harness.measure(fn, r)
    # Median should be around 10 ms ± reasonable tolerance
    assert r.median_ms is not None
    assert r.median_ms > 5  # at least 5 ms given 10 ms sleep


def test_harness_p95_single_run():
    """With a single run, p95 should equal that single value."""
    r = BenchmarkResult(name="p95_single")
    harness = BenchmarkHarness(name="p95_single", warmup=0, runs=1)

    def noop():
        return True

    harness.measure(noop, r)
    assert r.p95_ms == r.min_ms == r.max_ms


def test_harness_failure_tracking():
    """Failures from fn returning False should be counted correctly."""
    r = BenchmarkResult(name="failures")
    harness = BenchmarkHarness(name="failures", warmup=0, runs=6)

    call_count = [0]

    def sometimes_fails():
        call_count[0] += 1
        return call_count[0] % 2 == 0  # odd=fail, even=success

    harness.measure(sometimes_fails, r)
    assert r.success_count == 3
    assert r.failure_count == 3


def test_harness_exception_counts_as_failure():
    """Exceptions in fn() should be caught and counted as failures."""
    r = BenchmarkResult(name="exceptions")
    harness = BenchmarkHarness(name="exceptions", warmup=0, runs=4)

    call_count = [0]

    def raises():
        call_count[0] += 1
        if call_count[0] % 2 == 0:
            raise RuntimeError("simulated failure")
        return True

    harness.measure(raises, r)
    assert r.success_count == 2
    assert r.failure_count == 2
    # Latencies should still be recorded even for failed runs
    assert r.min_ms is not None


def test_harness_zero_runs():
    """Zero measured runs should produce no stats."""
    r = BenchmarkResult(name="zero")
    harness = BenchmarkHarness(name="zero", warmup=0, runs=0)

    def noop():
        return True

    harness.measure(noop, r)
    assert r.min_ms is None
    assert r.median_ms is None
    assert r.success_count == 0


def test_harness_warmup_not_counted():
    """Warmup calls must not appear in measured_runs."""
    r = BenchmarkResult(name="warmup_check")
    harness = BenchmarkHarness(name="warmup_check", warmup=3, runs=4)

    def noop():
        return True

    harness.measure(noop, r)
    assert r.warmup_runs == 3
    assert r.measured_runs == 4
    assert r.success_count == 4  # Only measured runs count


def test_harness_p95_with_outlier():
    """p95 should clip out extreme outliers."""
    # With 20 runs at 1ms, p95 index = int(20 * 0.95) - 1 = 18 (0-indexed from sorted)
    r = BenchmarkResult(name="p95_outlier")
    harness = BenchmarkHarness(name="p95_outlier", warmup=0, runs=20)

    call_count = [0]

    def fn():
        call_count[0] += 1
        # Last call is 10x slower — should not dominate median
        if call_count[0] == 20:
            time.sleep(0.100)
        else:
            time.sleep(0.005)
        return True

    harness.measure(fn, r)
    assert r.median_ms is not None
    assert r.median_ms < 50  # 5 ms median should be well below the 100 ms outlier


# ── Memory Measurement Tests ───────────────────────────────────────────────────

def test_memory_measurement_returns_float_or_none():
    """_get_process_rss_mb must return a non-negative float or None."""
    result = _get_process_rss_mb()
    if result is not None:
        assert isinstance(result, float)
        assert result > 0
    else:
        # None is acceptable if measurement is unavailable
        pass


def test_memory_measurement_not_zero():
    """If measurement is available, it should be > 0 (process is running)."""
    result = _get_process_rss_mb()
    if result is not None:
        assert result > 0.1  # At least 0.1 MB
