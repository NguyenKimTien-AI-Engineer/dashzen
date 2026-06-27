from __future__ import annotations

import json
from collections.abc import AsyncGenerator

import httpx

from core.llm.providers.openai import _build_tools, _messages_to_openai
from core.llm.types import LLMDelta, LLMMessage, ToolDefinition

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterProvider:
    """OpenAI-compatible provider for https://openrouter.ai"""

    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        site_url: str = "http://localhost:3000",
        app_name: str = "DashZen Studio",
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._site_url = site_url
        self._app_name = app_name

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self._site_url,
            "X-Title": self._app_name,
        }

    async def chat(
        self,
        messages: list[LLMMessage],
        *,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> str:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                OPENROUTER_API_URL,
                headers=self._headers(),
                json={
                    "model": self._model,
                    "messages": _messages_to_openai(messages),
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            message = data["choices"][0]["message"]
            return message.get("content") or message.get("reasoning") or ""

    async def stream(
        self,
        messages: list[LLMMessage],
        tools: list[ToolDefinition],
        *,
        max_tokens: int = 8192,
        temperature: float = 0.7,
        thinking_enabled: bool = False,
    ) -> AsyncGenerator[LLMDelta, None]:
        payload: dict = {  # type: ignore[type-arg]
            "model": self._model,
            "messages": _messages_to_openai(messages),
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        if tools:
            payload["tools"] = _build_tools(tools)

        pending_tcs: dict[int, dict] = {}  # type: ignore[type-arg]
        emitted_tool_keys: set[str] = set()

        async with httpx.AsyncClient(timeout=600) as client:
            async with client.stream(
                "POST",
                OPENROUTER_API_URL,
                headers=self._headers(),
                json=payload,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    raw = line.removeprefix("data:").strip()
                    if raw == "[DONE]":
                        break
                    if not raw:
                        continue
                    try:
                        ev = json.loads(raw)
                    except json.JSONDecodeError:
                        continue

                    if ev.get("error"):
                        message = ev["error"].get("message", "OpenRouter stream error")
                        raise httpx.HTTPStatusError(
                            message,
                            request=resp.request,
                            response=resp,
                        )

                    for choice in ev.get("choices", []):
                        delta = choice.get("delta", {})
                        if delta.get("content"):
                            yield LLMDelta(kind="text_delta", text=delta["content"])
                        if delta.get("reasoning"):
                            yield LLMDelta(kind="thinking_delta", thinking=delta["reasoning"])
                        for tc in delta.get("tool_calls", []):
                            idx = tc.get("index", 0)
                            fn = tc.get("function", {})
                            if idx not in pending_tcs:
                                pending_tcs[idx] = {
                                    "id": tc.get("id") or "",
                                    "name": fn.get("name", ""),
                                    "args": "",
                                }
                            if tc.get("id"):
                                pending_tcs[idx]["id"] = tc["id"]
                            if fn.get("name"):
                                pending_tcs[idx]["name"] = fn["name"]
                            pending_tcs[idx]["args"] += fn.get("arguments", "")

                        finish_reason = choice.get("finish_reason")
                        if finish_reason == "tool_calls":
                            for tc in pending_tcs.values():
                                dedupe = f"{tc['id']}:{tc['name']}:{tc['args']}"
                                if dedupe in emitted_tool_keys:
                                    continue
                                emitted_tool_keys.add(dedupe)
                                yield LLMDelta(
                                    kind="tool_call",
                                    tool_call_id=tc["id"] or None,
                                    tool_name=tc["name"],
                                    tool_args_json=tc["args"],
                                )
                            pending_tcs = {}

                    usage = ev.get("usage")
                    if usage:
                        yield LLMDelta(
                            kind="done",
                            prompt_tokens=usage.get("prompt_tokens"),
                            output_tokens=usage.get("completion_tokens"),
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
