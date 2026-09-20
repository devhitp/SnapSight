"""
Real OCR smoke test using EasyOCR on a controlled generated image.
NOT committed - run manually or in CI with OCR dependencies installed.
"""
import sys
import time

def run_smoke_test():
    try:
        from PIL import Image, ImageDraw, ImageFont
        import numpy as np
    except ImportError as e:
        print(f"SKIP: Pillow/numpy not available: {e}")
        return

    try:
        import easyocr
    except ImportError:
        print("SKIP: easyocr not installed.")
        return

    # Generate a controlled image with known text
    img = Image.new("RGB", (400, 100), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    known_text = "SnapSight OCR"
    draw.text((20, 30), known_text, fill=(0, 0, 0))

    np_img = np.array(img)

    print("Initializing EasyOCR reader (may download models on first run)...")
    t0 = time.perf_counter()
    reader = easyocr.Reader(['en'], gpu=False)
    init_ms = (time.perf_counter() - t0) * 1000

    print(f"EasyOCR initialized in {init_ms:.0f} ms")

    t1 = time.perf_counter()
    results = reader.readtext(np_img, detail=1)
    inference_ms = (time.perf_counter() - t1) * 1000

    print(f"Inference time: {inference_ms:.0f} ms")
    print(f"Results: {results}")

    detected_texts = [r[1].lower() for r in results]
    full = " ".join(detected_texts)
    print(f"Detected text: {full!r}")

    if "snapsight" in full or "ocr" in full:
        print("SMOKE TEST PASSED: Expected text detected.")
        return True
    else:
        print(f"SMOKE TEST PARTIAL: Text detected but did not match expected. Got: {full!r}")
        return False

if __name__ == "__main__":
    result = run_smoke_test()
    sys.exit(0 if result else 1)
