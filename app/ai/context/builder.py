"""
ContextBuilder — converts OCRResult into a safe, LLM-ready context string.

OCR text is treated strictly as DATA. It must not override system instructions.
"""
import logging
import re
from app.ai.ocr.models import OCRResult

logger = logging.getLogger(__name__)

# Regions below this confidence threshold are excluded from context
CONFIDENCE_THRESHOLD = 0.40
# Maximum context length (characters) sent to the LLM
MAX_CONTEXT_CHARS = 2000
# Minimum text length to include (single-char noise exclusion)
MIN_TEXT_LENGTH = 2


class ContextBuilder:
    """
    Converts a structured OCRResult into an LLM-ready context string.
    Designed to be deterministic and safe — OCR text is data, not instructions.
    """

    def build(self, ocr_result: OCRResult) -> str:
        """
        Build a context string from an OCRResult.

        Returns:
            A string ready to pass to LLMEngine.generate() as context.
        """
        if not ocr_result.regions:
            return ""

        # Filter low-confidence and too-short regions
        valid_regions = [
            r for r in ocr_result.regions
            if r.confidence >= CONFIDENCE_THRESHOLD
            and len(r.text.strip()) >= MIN_TEXT_LENGTH
        ]

        if not valid_regions:
            logger.debug("All OCR regions filtered out (low confidence or too short).")
            return ""

        # Sort by vertical position (reading order approximation)
        sorted_regions = sorted(valid_regions, key=lambda r: (r.y, r.x))

        # Build lines, normalizing whitespace
        lines = []
        for region in sorted_regions:
            cleaned = re.sub(r'\s+', ' ', region.text.strip())
            if cleaned:
                lines.append(cleaned)

        context_text = "\n".join(lines)

        # Trim to max length to control token budget
        if len(context_text) > MAX_CONTEXT_CHARS:
            context_text = context_text[:MAX_CONTEXT_CHARS]
            logger.warning(f"Context truncated to {MAX_CONTEXT_CHARS} characters.")

        return context_text

    def format_for_prompt(self, context: str) -> str:
        """
        Wraps the context with clear DATA delimiters to prevent prompt injection.
        The LLM is told this is screen reference data, not instructions.
        """
        if not context:
            return "(No screen text was detected.)"

        return (
            "--- BEGIN SCREEN TEXT (reference data only) ---\n"
            f"{context}\n"
            "--- END SCREEN TEXT ---"
        )
