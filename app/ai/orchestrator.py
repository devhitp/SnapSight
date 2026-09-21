import logging
from typing import Optional
from dataclasses import dataclass
from app.ai.router.models import QuestionIntent, ContextRequirement, RouteDecision
from app.ai.router.router import QuestionRouter
from app.ai.llm.engine import LLMEngine
from app.ai.vision.engine import VisionEngine
from app.ai.context.builder import ContextBuilder
from app.capture.models import CaptureResult
from app.ai.ocr.models import OCRResult

logger = logging.getLogger(__name__)

@dataclass
class AIOrchestratorResult:
    answer: str
    route_used: QuestionIntent
    backend_used: str
    inference_time_ms: float
    ocr_used: bool
    vision_used: bool
    success: bool
    error: Optional[str] = None

class AIOrchestrator:
    """
    Coordinates routing, context selection, and model inference.
    """
    def __init__(self, llm_engine: LLMEngine, vision_engine: VisionEngine):
        self.router = QuestionRouter()
        self.context_builder = ContextBuilder()
        self.llm_engine = llm_engine
        self.vision_engine = vision_engine

    def ask(self, question: str, capture: Optional[CaptureResult], ocr: Optional[OCRResult]) -> AIOrchestratorResult:
        try:
            decision = self.router.route(question)
            logger.info(f"Routed question to {decision.intent.name} (confidence: {decision.confidence})")

            ocr_context = ""
            if ocr and decision.context_requirement in [ContextRequirement.OCR_ONLY, ContextRequirement.OCR_AND_IMAGE]:
                raw_context = self.context_builder.build(ocr)
                ocr_context = self.context_builder.format_for_prompt(raw_context)

            # Routing execution
            if decision.intent == QuestionIntent.VISUAL:
                return self._handle_vision(question, capture, decision)
                
            elif decision.intent == QuestionIntent.MIXED:
                # If vision backend is available, we might want to use it alongside LLM.
                # Since vision is not available, we can fallback to LLM with OCR.
                # We could query Vision first and then pass the result to LLM, but for Sprint 5:
                # If Vision is available, we use Vision. Else we fallback to OCR+LLM.
                if self.vision_engine.is_available and capture:
                    return self._handle_vision(question, capture, decision, ocr_context)
                else:
                    return self._handle_llm(question, ocr_context, decision)
                    
            elif decision.intent == QuestionIntent.GENERAL:
                # No OCR context required
                return self._handle_llm(question, "", decision)
                
            else: # TEXT, CODE, UNSUPPORTED
                return self._handle_llm(question, ocr_context, decision)

        except Exception as e:
            logger.error(f"Orchestrator error: {e}")
            return AIOrchestratorResult(
                answer="",
                route_used=QuestionIntent.UNSUPPORTED,
                backend_used="Unknown",
                inference_time_ms=0.0,
                ocr_used=False,
                vision_used=False,
                success=False,
                error=str(e)
            )

    def _handle_llm(self, question: str, context: str, decision: RouteDecision) -> AIOrchestratorResult:
        if not self.llm_engine.is_available:
            return AIOrchestratorResult(
                answer="",
                route_used=decision.intent,
                backend_used="None",
                inference_time_ms=0.0,
                ocr_used=bool(context),
                vision_used=False,
                success=False,
                error="LLM Engine is unavailable."
            )
            
        result = self.llm_engine.generate(question, context)
        return AIOrchestratorResult(
            answer=result.answer,
            route_used=decision.intent,
            backend_used=f"Local LLM ({self.llm_engine.model_name})",
            inference_time_ms=result.generation_time_ms,
            ocr_used=bool(context),
            vision_used=False,
            success=result.success,
            error=result.error
        )

    def _handle_vision(self, question: str, capture: Optional[CaptureResult], decision: RouteDecision, additional_context: str = "") -> AIOrchestratorResult:
        if not capture or not capture.is_valid:
            return AIOrchestratorResult(
                answer="",
                route_used=decision.intent,
                backend_used=self.vision_engine.engine_name,
                inference_time_ms=0.0,
                ocr_used=bool(additional_context),
                vision_used=True,
                success=False,
                error="No valid screen capture provided for visual analysis."
            )
            
        # Combine question with additional text context if mixed
        full_question = question
        if additional_context:
            full_question = f"{additional_context}\n\nQuestion: {question}"
            
        result = self.vision_engine.analyze_image(capture.image, full_question)
        
        return AIOrchestratorResult(
            answer=result.answer,
            route_used=decision.intent,
            backend_used=result.backend,
            inference_time_ms=result.inference_time_ms,
            ocr_used=bool(additional_context),
            vision_used=True,
            success=result.success,
            error=result.error
        )
