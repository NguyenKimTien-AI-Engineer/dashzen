from core.llm.providers.vilao import _thinking_text, _usage_tokens


def test_usage_tokens_supports_openai_fields() -> None:
    prompt, completion = _usage_tokens({"usage": {"prompt_tokens": 120, "completion_tokens": 45}})
    assert prompt == 120
    assert completion == 45


def test_usage_tokens_supports_input_output_fields() -> None:
    prompt, completion = _usage_tokens({"usage": {"input_tokens": 88, "output_tokens": 12}})
    assert prompt == 88
    assert completion == 12


def test_thinking_text_accepts_reasoning_variants() -> None:
    assert _thinking_text({"reasoning": "Plan response"}) == "Plan response"
    assert _thinking_text({"reasoning_content": "Hidden thoughts"}) == "Hidden thoughts"
    assert _thinking_text({"content": "No reasoning"}) is None
