from __future__ import annotations

import httpx

from core.llm.thinking import (
    deltas_from_ollama_message,
    is_ollama_think_rejection,
    resolve_ollama_think_param,
    resolve_thinking_enabled,
)
from core.llm.types import LLMDelta


def test_resolve_thinking_enabled_explicit_request() -> None:
    assert resolve_thinking_enabled(
        True, provider="ollama", ollama_thinking_enabled=False
    )
    assert not resolve_thinking_enabled(
        False, provider="ollama", ollama_thinking_enabled=True
    )


def test_resolve_thinking_enabled_ollama_default() -> None:
    assert resolve_thinking_enabled(
        None, provider="ollama", ollama_thinking_enabled=True
    )
    assert not resolve_thinking_enabled(
        None, provider="ollama", ollama_thinking_enabled=False
    )


def test_resolve_thinking_enabled_other_providers_default_off() -> None:
    assert not resolve_thinking_enabled(
        None, provider="anthropic", ollama_thinking_enabled=True
    )


def test_resolve_ollama_think_param_disabled() -> None:
    assert resolve_ollama_think_param(enabled=False, level="", model="qwen3") is None


def test_resolve_ollama_think_param_default_true() -> None:
    assert resolve_ollama_think_param(enabled=True, level="", model="qwen3") is True


def test_resolve_ollama_think_param_level() -> None:
    assert resolve_ollama_think_param(enabled=True, level="high", model="qwen3") == "high"


def test_resolve_ollama_think_param_gpt_oss() -> None:
    assert (
        resolve_ollama_think_param(enabled=True, level="", model="gpt-oss:20b")
        == "medium"
    )
    assert (
        resolve_ollama_think_param(enabled=True, level="low", model="gpt-oss")
        == "low"
    )


def test_deltas_from_ollama_message_thinking_before_content() -> None:
    deltas = deltas_from_ollama_message({
        "thinking": "Let me reason",
        "content": "Answer",
    })
    assert [d.kind for d in deltas] == ["thinking_delta", "text_delta"]
    assert deltas[0].thinking == "Let me reason"
    assert deltas[1].text == "Answer"


def test_deltas_from_ollama_message_tool_calls() -> None:
    deltas = deltas_from_ollama_message({
        "content": "",
        "tool_calls": [
            {
                "function": {
                    "name": "read_file",
                    "arguments": {"path": "spec.md"},
                }
            }
        ],
    })
    assert len(deltas) == 1
    assert deltas[0].kind == "tool_call"
    assert deltas[0].tool_name == "read_file"


def test_is_ollama_think_rejection() -> None:
    request = httpx.Request("POST", "http://localhost:11434/api/chat")
    response = httpx.Response(400, request=request, text="think not supported")
    exc = httpx.HTTPStatusError("bad", request=request, response=response)
    assert is_ollama_think_rejection(exc)

    response_ok = httpx.Response(500, request=request, text="server error")
    exc_ok = httpx.HTTPStatusError("bad", request=request, response=response_ok)
    assert not is_ollama_think_rejection(exc_ok)


def test_deltas_from_ollama_message_empty() -> None:
    assert deltas_from_ollama_message({}) == []
