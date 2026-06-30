from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from typing import Any

import httpx

from core.llm.providers.openai import _build_tools, _messages_to_openai
from core.llm.types import LLMChatResult, LLMDelta, LLMMessage, LLMUsage, ToolDefinition


def _extract_error_message(body: bytes) -> str | None:
    if not body:
        return None
    try:
        payload = json.loads(body.decode("utf-8", errors="ignore"))
    except json.JSONDecodeError:
        text = body.decode("utf-8", errors="ignore").strip()
        return text[:300] if text else None
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict):
            message = error.get("message")
            if isinstance(message, str) and message.strip():
                return message.strip()
        detail = payload.get("detail")
        if isinstance(detail, str) and detail.strip():
            return detail.strip()
    return None


def _usage_tokens(payload: dict[str, Any]) -> tuple[int | None, int | None]:
    usage = payload.get("usage") or {}
    prompt_tokens = usage.get("prompt_tokens") or usage.get("input_tokens")
    completion_tokens = usage.get("completion_tokens") or usage.get("output_tokens")
    return prompt_tokens, completion_tokens


def _thinking_text(delta: dict[str, Any]) -> str | None:
    value = delta.get("reasoning") or delta.get("reasoning_content")
    if isinstance(value, str) and value:
        return value
    return None


class VilaoProvider:
    """OpenAI-compatible provider for https://api.vilao.ai."""

    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        base_url: str = "https://api.vilao.ai/v1",
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._chat_url = f"{base_url.rstrip('/')}/chat/completions"

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}

    async def chat(
        self,
        messages: list[LLMMessage],
        *,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> LLMChatResult:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                self._chat_url,
                headers=self._headers(),
                json={
                    "model": self._model,
                    "messages": _messages_to_openai(messages),
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
            )
            if resp.status_code >= 400:
                provider_error = _extract_error_message(resp.content)
                if provider_error:
                    raise httpx.HTTPStatusError(
                        provider_error,
                        request=resp.request,
                        response=resp,
                    )
            resp.raise_for_status()
            data = resp.json()
            message = data["choices"][0]["message"]
            prompt_tokens, completion_tokens = _usage_tokens(data)
            return LLMChatResult(
                content=message.get("content") or message.get("reasoning") or "",
                usage=LLMUsage(
                    input_tokens=prompt_tokens,
                    output_tokens=completion_tokens,
                ),
            )

    async def stream(
        self,
        messages: list[LLMMessage],
        tools: list[ToolDefinition],
        *,
        max_tokens: int = 8192,
        temperature: float = 0.7,
        thinking_enabled: bool = False,
    ) -> AsyncGenerator[LLMDelta, None]:
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": _messages_to_openai(messages),
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }
        if tools:
            payload["tools"] = _build_tools(tools)

        pending_tcs: dict[int, dict[str, str]] = {}

        async with httpx.AsyncClient(timeout=600) as client:
            async with client.stream(
                "POST",
                self._chat_url,
                headers=self._headers(),
                json=payload,
            ) as resp:
                if resp.status_code >= 400:
                    body = await resp.aread()
                    provider_error = _extract_error_message(body)
                    if provider_error:
                        raise httpx.HTTPStatusError(
                            provider_error,
                            request=resp.request,
                            response=resp,
                        )
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    raw = line.removeprefix("data:").strip()
                    if raw in ("", "[DONE]"):
                        break
                    try:
                        ev = json.loads(raw)
                    except json.JSONDecodeError:
                        continue

                    if ev.get("error"):
                        message = ev["error"].get("message", "VILAO stream error")
                        raise httpx.HTTPStatusError(message, request=resp.request, response=resp)

                    for choice in ev.get("choices", []):
                        delta = choice.get("delta", {})
                        if delta.get("content"):
                            yield LLMDelta(kind="text_delta", text=delta["content"])
                        thinking = _thinking_text(delta)
                        if thinking_enabled and thinking:
                            yield LLMDelta(kind="thinking_delta", thinking=thinking)
                        for tc in delta.get("tool_calls", []):
                            idx = tc.get("index", 0)
                            fn = tc.get("function", {})
                            if idx not in pending_tcs:
                                pending_tcs[idx] = {"id": "", "name": "", "args": ""}
                            if tc.get("id"):
                                pending_tcs[idx]["id"] = tc["id"]
                            if fn.get("name"):
                                pending_tcs[idx]["name"] = fn["name"]
                            pending_tcs[idx]["args"] += fn.get("arguments", "")
                        if choice.get("finish_reason") == "tool_calls":
                            for tc in pending_tcs.values():
                                yield LLMDelta(
                                    kind="tool_call",
                                    tool_call_id=tc["id"] or None,
                                    tool_name=tc["name"],
                                    tool_args_json=tc["args"],
                                )
                            pending_tcs = {}

                    prompt_tokens, completion_tokens = _usage_tokens(ev)
                    if prompt_tokens is not None or completion_tokens is not None:
                        yield LLMDelta(
                            kind="done",
                            prompt_tokens=prompt_tokens,
                            output_tokens=completion_tokens,
                        )
                        return

                if pending_tcs:
                    for tc in pending_tcs.values():
                        yield LLMDelta(
                            kind="tool_call",
                            tool_call_id=tc["id"] or None,
                            tool_name=tc["name"],
                            tool_args_json=tc["args"],
                        )

                yield LLMDelta(kind="done")
