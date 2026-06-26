from __future__ import annotations

import json
from collections.abc import AsyncGenerator

import httpx

from core.llm.types import LLMDelta, LLMMessage, ToolDefinition


def _build_tools(tools: list[ToolDefinition]) -> list[dict]:  # type: ignore[type-arg]
    return [
        {"name": t.name, "description": t.description, "input_schema": t.parameters} for t in tools
    ]


def _messages_to_anthropic(
    messages: list[LLMMessage],
) -> tuple[str | None, list[dict]]:  # type: ignore[type-arg]
    system: str | None = None
    out = []
    for m in messages:
        if m.role == "system":
            if isinstance(m.content, str):
                system = m.content
            continue
        if m.role == "tool":
            out.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": m.tool_call_id,
                            "content": m.content if isinstance(m.content, str) else str(m.content),
                        }
                    ],
                }
            )
        elif m.tool_calls:
            content_blocks = []
            if isinstance(m.content, str) and m.content:
                content_blocks.append({"type": "text", "text": m.content})
            for tc in m.tool_calls:
                content_blocks.append(
                    {
                        "type": "tool_use",
                        "id": tc.get("id"),
                        "name": tc.get("name"),
                        "input": tc.get("input", {}),
                    }
                )
            out.append({"role": "assistant", "content": content_blocks})
        else:
            content = m.content if isinstance(m.content, str) else str(m.content)
            out.append({"role": m.role, "content": content})
    return system, out


class AnthropicProvider:
    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

    def _headers(self) -> dict[str, str]:
        return {
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

    async def chat(
        self,
        messages: list[LLMMessage],
        *,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> str:
        system, msgs = _messages_to_anthropic(messages)
        payload: dict = {  # type: ignore[type-arg]
            "model": self._model,
            "messages": msgs,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system:
            payload["system"] = system
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers=self._headers(),
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            for block in data.get("content", []):
                if block.get("type") == "text":
                    return block["text"]
        return ""

    async def stream(
        self,
        messages: list[LLMMessage],
        tools: list[ToolDefinition],
        *,
        max_tokens: int = 8192,
        temperature: float = 0.7,
        thinking_enabled: bool = False,
    ) -> AsyncGenerator[LLMDelta, None]:
        system, msgs = _messages_to_anthropic(messages)
        payload: dict = {  # type: ignore[type-arg]
            "model": self._model,
            "messages": msgs,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }
        if system:
            payload["system"] = system
        if tools:
            payload["tools"] = _build_tools(tools)

        pending_tool: dict = {}  # type: ignore[type-arg]
        prompt_tokens: int | None = None
        output_tokens: int | None = None

        async with httpx.AsyncClient(timeout=600) as client:
            async with client.stream(
                "POST",
                "https://api.anthropic.com/v1/messages",
                headers=self._headers(),
                json=payload,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    raw = line.removeprefix("data:").strip()
                    if raw in ("", "[DONE]"):
                        continue
                    try:
                        ev = json.loads(raw)
                    except json.JSONDecodeError:
                        continue

                    etype = ev.get("type")
                    if etype == "content_block_start":
                        block = ev.get("content_block", {})
                        if block.get("type") == "tool_use":
                            pending_tool = {
                                "id": block.get("id"),
                                "name": block.get("name"),
                                "args_json": "",
                            }
                    elif etype == "content_block_delta":
                        delta = ev.get("delta", {})
                        dtype = delta.get("type")
                        if dtype == "text_delta":
                            yield LLMDelta(kind="text_delta", text=delta.get("text", ""))
                        elif dtype == "thinking_delta":
                            yield LLMDelta(
                                kind="thinking_delta", thinking=delta.get("thinking", "")
                            )
                        elif dtype == "input_json_delta":
                            pending_tool["args_json"] = pending_tool.get(
                                "args_json", ""
                            ) + delta.get("partial_json", "")
                    elif etype == "content_block_stop":
                        if pending_tool.get("id"):
                            yield LLMDelta(
                                kind="tool_call",
                                tool_call_id=pending_tool["id"],
                                tool_name=pending_tool["name"],
                                tool_args_json=pending_tool.get("args_json", "{}"),
                            )
                            pending_tool = {}
                    elif etype == "message_start":
                        usage = ev.get("message", {}).get("usage", {})
                        prompt_tokens = usage.get("input_tokens")
                    elif etype == "message_delta":
                        usage = ev.get("usage", {})
                        output_tokens = usage.get("output_tokens")
                    elif etype == "message_stop":
                        yield LLMDelta(
                            kind="done",
                            prompt_tokens=prompt_tokens,
                            output_tokens=output_tokens,
                        )
