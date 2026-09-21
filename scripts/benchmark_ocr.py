"""
Backward-compatible OCR benchmark entry point.
Delegates to the unified scripts/benchmark.py --ocr.

Usage:
    python scripts/benchmark_ocr.py

For more options including LLM, router, and e2e benchmarks:
    python scripts/benchmark.py --help
"""
import os
import sys

# Ensure the project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Delegate to the unified benchmark with --ocr flag
sys.argv = [sys.argv[0], "--ocr"]

from scripts.benchmark import main  # noqa: E402

if __name__ == "__main__":
    main()
