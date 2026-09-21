import re
from .models import QuestionIntent, ContextRequirement, RouteDecision

class QuestionRouter:
    """
    Deterministic router that categorizes user questions into intents
    and determines the required context.
    """

    VISUAL_KEYWORDS = [
        "color", "look like", "where is", "which icon", "what object", 
        "what image", "what graph", "what chart", "what button", "what logo", 
        "describe the image", "what is shown"
    ]

    CODE_KEYWORDS = [
        "error", "exception", "stack trace", "bug", "code", "function", 
        "variable", "syntax", "compile", "traceback", "python", "javascript", 
        "c++", "java", "html", "css"
    ]

    TEXT_KEYWORDS = [
        "what does it say", "read", "deadline", "date", "price", "name", 
        "title", "text", "summarize this page"
    ]

    MIXED_KEYWORDS = [
        "explain this graph", "summarize this screen", "what is this page about",
        "explain what is happening here", "explain what this graph"
    ]

    def _matches_keywords(self, text: str, keywords: list[str]) -> bool:
        text = text.lower()
        return any(kw.lower() in text for kw in keywords)

    def route(self, question: str) -> RouteDecision:
        q_lower = question.lower().strip()
        
        if not q_lower:
            return RouteDecision(
                intent=QuestionIntent.UNSUPPORTED,
                context_requirement=ContextRequirement.NONE,
                confidence=1.0,
                reason="Empty question"
            )

        # 1. Mixed
        if self._matches_keywords(q_lower, self.MIXED_KEYWORDS):
            return RouteDecision(
                intent=QuestionIntent.MIXED,
                context_requirement=ContextRequirement.OCR_AND_IMAGE,
                confidence=0.8,
                reason="Matched mixed-intent keyword"
            )
            
        # 2. Visual
        if self._matches_keywords(q_lower, self.VISUAL_KEYWORDS):
            return RouteDecision(
                intent=QuestionIntent.VISUAL,
                context_requirement=ContextRequirement.IMAGE_ONLY,
                confidence=0.8,
                reason="Matched visual keyword"
            )
            
        # 3. Code
        if self._matches_keywords(q_lower, self.CODE_KEYWORDS):
            return RouteDecision(
                intent=QuestionIntent.CODE,
                context_requirement=ContextRequirement.OCR_ONLY,
                confidence=0.8,
                reason="Matched code/error keyword"
            )
            
        # 4. Text
        if self._matches_keywords(q_lower, self.TEXT_KEYWORDS):
            return RouteDecision(
                intent=QuestionIntent.TEXT,
                context_requirement=ContextRequirement.OCR_ONLY,
                confidence=0.8,
                reason="Matched text keyword"
            )
            
        # 5. Explicit reference to screen but no specific visual/code/text keyword
        screen_keywords = ["screen", "page", "here", "this", "my display", "monitor"]
        if self._matches_keywords(q_lower, screen_keywords):
            return RouteDecision(
                intent=QuestionIntent.TEXT,  # default to OCR for ambiguous screen reference
                context_requirement=ContextRequirement.OCR_ONLY,
                confidence=0.5,
                reason="Ambiguous screen reference, defaulting to OCR"
            )
            
        # 6. General question without screen references
        return RouteDecision(
            intent=QuestionIntent.GENERAL,
            context_requirement=ContextRequirement.NONE,
            confidence=0.7,
            reason="No screen references detected, treating as general query"
        )
