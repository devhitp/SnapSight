import pytest
from app.ai.router.router import QuestionRouter
from app.ai.router.models import QuestionIntent, ContextRequirement

def test_router_empty_question():
    router = QuestionRouter()
    decision = router.route("")
    assert decision.intent == QuestionIntent.UNSUPPORTED
    assert decision.context_requirement == ContextRequirement.NONE

def test_router_visual_question():
    router = QuestionRouter()
    decision = router.route("What color is the button?")
    assert decision.intent == QuestionIntent.VISUAL
    assert decision.context_requirement == ContextRequirement.IMAGE_ONLY
    
def test_router_code_question():
    router = QuestionRouter()
    decision = router.route("Why is there a python traceback here?")
    assert decision.intent == QuestionIntent.CODE
    assert decision.context_requirement == ContextRequirement.OCR_ONLY

def test_router_text_question():
    router = QuestionRouter()
    decision = router.route("What does the title say?")
    assert decision.intent == QuestionIntent.TEXT
    assert decision.context_requirement == ContextRequirement.OCR_ONLY

def test_router_mixed_question():
    router = QuestionRouter()
    decision = router.route("Summarize this screen.")
    assert decision.intent == QuestionIntent.MIXED
    assert decision.context_requirement == ContextRequirement.OCR_AND_IMAGE

def test_router_general_question():
    router = QuestionRouter()
    decision = router.route("What is the capital of France?")
    assert decision.intent == QuestionIntent.GENERAL
    assert decision.context_requirement == ContextRequirement.NONE

def test_router_ambiguous_screen_reference():
    router = QuestionRouter()
    decision = router.route("Explain this to me.")
    assert decision.intent == QuestionIntent.TEXT
    assert decision.context_requirement == ContextRequirement.OCR_ONLY
