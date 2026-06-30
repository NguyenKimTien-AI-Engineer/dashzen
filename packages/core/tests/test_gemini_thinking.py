from core.llm.providers.gemini import deltas_from_gemini_parts
from core.llm.thinking import resolve_thinking_enabled


def test_resolve_thinking_enabled_gemini_default_on() -> None:
    assert resolve_thinking_enabled(None, provider="gemini", ollama_thinking_enabled=False)


def test_deltas_from_gemini_parts_thought_before_answer() -> None:
    parts = [
        {"text": "Let me check the request scope.", "thought": True},
        {"text": "I cannot write creative essays."},
    ]
    deltas = deltas_from_gemini_parts(parts)
    assert [d.kind for d in deltas] == ["thinking_delta", "text_delta"]
    assert deltas[0].thinking == "Let me check the request scope."
    assert deltas[1].text == "I cannot write creative essays."
