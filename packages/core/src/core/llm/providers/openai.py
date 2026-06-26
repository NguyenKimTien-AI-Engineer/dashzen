from __future__ import annotations

import json
from collections.abc import AsyncGenerator

import httpx

from core.llm.types import LLMDelta, LLMMessage, ToolDefinition


def _build_tools(tools: list[ToolDefinition]) -> list[dict]:  # type: ignore[type-arg]
    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
            },
        }
        for t in tools
    ]


def _messages_to_openai(messages: list[LLMMessage]) -> list[dict]:  # type: ignore[type-arg]
    out = []
    for m in messages:
        if m.role == "tool":
            out.append(
                {
                    "role": "tool",
                    "tool_call_id": m.tool_call_id,
                    "content": m.content if isinstance(m.content, str) else str(m.content),
                }
            )
        elif m.tool_calls:
            out.append(
                {
                    "role": "assistant",
                    "content": m.content if isinstance(m.content, str) else None,
                    "tool_calls": m.tool_calls,
                }
            )
        else:
            out.append(
                {
                    "role": m.role,
                    "content": m.content if isinstance(m.content, str) else str(m.content),
                }
            )
    return out


class OpenAIProvider:
    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}", "content-type": "application/json"}

    async def chat(
        self,
        messages: list[LLMMessage],
        *,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> str:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
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
            return data["choices"][0]["message"]["content"] or ""

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

        async with httpx.AsyncClient(timeout=600) as client:
            async with client.stream(
                "POST",
                "https://api.openai.com/v1/chat/completions",
                headers=self._headers(),
                json=payload,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    raw = line.removeprefix("data:").strip()
                    if raw == "[DONE]":
                        yield LLMDelta(kind="done")
                        return
                    try:
                        ev = json.loads(raw)
                    except json.JSONDecodeError:
                        continue

                    usage = ev.get("usage")
                    if usage:
                        yield LLMDelta(
                            kind="done",
                            prompt_tokens=usage.get("prompt_tokens"),
                            output_tokens=usage.get("completion_tokens"),
                        )
                        return

                    for choice in ev.get("choices", []):
                        delta = choice.get("delta", {})
                        if delta.get("content"):
                            yield LLMDelta(kind="text_delta", text=delta["content"])
                        for tc in delta.get("tool_calls", []):
                            idx = tc.get("index", 0)
                            fn = tc.get("function", {})
                            if idx not in pending_tcs:
                                pending_tcs[idx] = {
                                    "id": tc.get("id", ""),
                                    "name": fn.get("name", ""),
                                    "args": "",
                                }
                            pending_tcs[idx]["args"] += fn.get("arguments", "")
                        if choice.get("finish_reason") == "tool_calls":
                            for tc in pending_tcs.values():
                                yield LLMDelta(
                                    kind="tool_call",
                                    tool_call_id=tc["id"],
                                    tool_name=tc["name"],
                                    tool_args_json=tc["args"],
                                )
                            pending_tcs = {}
