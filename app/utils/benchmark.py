"""
SnapSight Benchmark Harness (Sprint 8).

Provides typed data models and a reusable timing harness for measuring
OCR, LLM, router and end-to-end performance.

All timing uses time.perf_counter() — monotonic, high-resolution.
Memory uses psutil RSS where available, with graceful fallback.

PRIVACY:
- BenchmarkResult stores only metadata and timing measurements.
- It never stores screenshot pixels, OCR text, user questions,
  model prompts, or any private screen content.
"""
from __future__ import annotations

import os
import platform
import statistics
import time
from dataclasses import dataclass, field, asdict
from typing import Callable, List, Optional


# ── Memory measurement ────────────────────────────────────────────────────────

def _get_process_rss_mb() -> Optional[float]:
    """
    Return current process RSS (Resident Set Size) in MB.
    Uses psutil if available; falls back to Windows ctypes; returns None on failure.
    RSS is process memory as reported by the OS and is an approximation of
    physical RAM usage — not an exact breakdown per subsystem.
    """
    try:
        import psutil
        return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
    except ImportError:
        pass

    # Windows ctypes fallback
    try:
        import ctypes
        import ctypes.wintypes

        class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
            _fields_ = [
                ("cb", ctypes.wintypes.DWORD),
                ("PageFaultCount", ctypes.wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage2", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        pmc = PROCESS_MEMORY_COUNTERS()
        pmc.cb = ctypes.sizeof(pmc)
        handle = ctypes.windll.kernel32.GetCurrentProcess()
        if ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(pmc), pmc.cb):
            return pmc.WorkingSetSize / (1024 * 1024)
    except Exception:
        pass

    return None


def get_machine_info() -> dict:
    """Return a dict of machine metadata for stamping benchmark results."""
    return {
        "cpu": platform.processor() or platform.machine(),
        "machine": platform.machine(),
        "platform": platform.system(),
        "python": platform.python_version(),
        "node": platform.node(),
    }


# ── Data Model ────────────────────────────────────────────────────────────────

@dataclass
class BenchmarkResult:
    """
    Typed record for a single benchmark run series.
    Stores only performance metadata — never private screen content.
    """
    name: str
    timestamp: float = field(default_factory=time.time)

    # Hardware identity
    machine: str = ""
    platform: str = ""
    architecture: str = ""
    cpu: str = ""

    # Runtime identity
    backend: str = ""
    runtime: str = ""
    accelerator: str = ""
    model: str = ""

    # Input description (no sensitive content)
    input_description: str = ""
    input_resolution: str = ""

    # Measurement parameters
    warmup_runs: int = 0
    measured_runs: int = 0

    # Latency stats (ms)
    min_ms: Optional[float] = None
    max_ms: Optional[float] = None
    mean_ms: Optional[float] = None
    median_ms: Optional[float] = None
    p95_ms: Optional[float] = None

    # Reliability
    success_count: int = 0
    failure_count: int = 0

    # Optional extras
    notes: str = ""

    def to_dict(self) -> dict:
        """Serialize to a plain dict safe for JSON output."""
        return asdict(self)


# ── Harness ───────────────────────────────────────────────────────────────────

class BenchmarkHarness:
    """
    Runs a callable N warmup times (results discarded) then M measured times.
    Records per-run latency using time.perf_counter().
    Computes min, max, mean, median, p95.
    """

    def __init__(self, name: str, warmup: int = 1, runs: int = 5):
        self.name = name
        self.warmup = warmup
        self.runs = runs

    def measure(
        self,
        fn: Callable[[], bool],
        result: BenchmarkResult,
    ) -> BenchmarkResult:
        """
        Execute fn() for warmup + measured runs, populating result in place.

        fn() should return True on success, False on failure.
        Exceptions in fn() are caught and counted as failures.

        Args:
            fn:     Zero-argument callable. Return True for success.
            result: BenchmarkResult to populate with stats.

        Returns:
            The populated BenchmarkResult.
        """
        result.warmup_runs = self.warmup
        result.measured_runs = self.runs

        # Warmup phase — not measured
        for _ in range(self.warmup):
            try:
                fn()
            except Exception:
                pass

        # Measurement phase
        latencies: List[float] = []
        successes = 0
        failures = 0

        for _ in range(self.runs):
            t0 = time.perf_counter()
            try:
                ok = fn()
                elapsed_ms = (time.perf_counter() - t0) * 1000.0
                latencies.append(elapsed_ms)
                if ok:
                    successes += 1
                else:
                    failures += 1
            except Exception:
                elapsed_ms = (time.perf_counter() - t0) * 1000.0
                latencies.append(elapsed_ms)
                failures += 1

        result.success_count = successes
        result.failure_count = failures

        if latencies:
            result.min_ms = min(latencies)
            result.max_ms = max(latencies)
            result.mean_ms = statistics.mean(latencies)
            result.median_ms = statistics.median(latencies)
            # p95: 95th percentile — use nearest-rank method
            sorted_lat = sorted(latencies)
            p95_idx = max(0, int(len(sorted_lat) * 0.95) - 1)
            result.p95_ms = sorted_lat[p95_idx]

        return result


def make_result(name: str, **kwargs) -> BenchmarkResult:
    """Convenience factory: create a BenchmarkResult pre-filled with machine info."""
    info = get_machine_info()
    return BenchmarkResult(
        name=name,
        machine=info["machine"],
        platform=info["platform"],
        architecture=info["machine"],
        cpu=info["cpu"],
        **kwargs,
    )
