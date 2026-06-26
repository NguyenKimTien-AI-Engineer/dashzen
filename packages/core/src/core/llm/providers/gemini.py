from __future__ import annotations

import json
import uuid
from collections.abc import AsyncGenerator
from typing import Any

import httpx

from core.llm.types import LLMDelta, LLMMessage, ToolDefinition

_GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


def _content_to_text(content: str | list[Any]) -> str:
    if isinstance(content, str):
        return content
    return " ".join(
        part.get("text", "") if isinstance(part, dict) else str(part) for part in content
    )


def _build_tools(tools: list[ToolDefinition]) -> list[dict[str, Any]]:
    if not tools:
        return []
    return [
        {
            "functionDeclarations": [
                {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                }
                for t in tools
            ]
        }
    ]


def _messages_to_gemini(
    messages: list[LLMMessage],
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    system_instruction: dict[str, Any] | None = None
    call_id_to_name: dict[str, str] = {}
    contents: list[dict[str, Any]] = []

    for message in messages:
        text = _content_to_text(message.content)

        if message.role == "system":
            if text:
                system_instruction = {"parts": [{"text": text}]}
            continue

        if message.role == "tool":
            fn_name = call_id_to_name.get(message.tool_call_id or "", "unknown")
            contents.append({
                "role": "user",
                "parts": [
                    {
                        "functionResponse": {
                            "name": fn_name,
                            "response": {"result": text},
                        }
                    }
                ],
            })
            continue

        if message.tool_calls:
            parts: list[dict[str, Any]] = []
            if text:
                parts.append({"text": text})
            for tool_call in message.tool_calls:
                call_id = str(tool_call.get("id", ""))
                fn_name = str(tool_call.get("name", ""))
                if call_id and fn_name:
                    call_id_to_name[call_id] = fn_name
                parts.append({
                    "functionCall": {
                        "name": fn_name,
                        "args": tool_call.get("input", {}),
                    }
                })
            contents.append({"role": "model", "parts": parts})
            continue

        role = "model" if message.role == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": text}]})

    return system_instruction, contents


class GeminiProvider:
    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

    def _headers(self) -> dict[str, str]:
        return {"x-goog-api-key": self._api_key, "content-type": "application/json"}

    def _model_url(self, action: str) -> str:
        return f"{_GEMINI_API_BASE}/{self._model}:{action}"

    def _build_payload(
        self,
        messages: list[LLMMessage],
        tools: list[ToolDefinition],
        *,
        max_tokens: int,
        temperature: float,
    ) -> dict[str, Any]:
        system_instruction, contents = _messages_to_gemini(messages)
        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": temperature,
            },
        }
        if system_instruction:
            payload["systemInstruction"] = system_instruction
        tool_payload = _build_tools(tools)
        if tool_payload:
            payload["tools"] = tool_payload
        return payload

    async def chat(
        self,
        messages: list[LLMMessage],
        *,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> str:
        payload = self._build_payload(
            messages, [], max_tokens=max_tokens, temperature=temperature
        )
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                self._model_url("generateContent"),
                headers=self._headers(),
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            for part in data.get("candidates", [{}])[0].get("content", {}).get("parts", []):
                if "text" in part:
                    return part["text"]
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
        payload = self._build_payload(
            messages, tools, max_tokens=max_tokens, temperature=temperature
        )
        prompt_tokens: int | None = None
        output_tokens: int | None = None
        emitted_tool_calls: set[str] = set()

        async with httpx.AsyncClient(timeout=600) as client:
            async with client.stream(
                "POST",
                self._model_url("streamGenerateContent"),
                headers=self._headers(),
                params={"alt": "sse"},
                json=payload,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    raw = line.removeprefix("data:").strip()
                    if not raw:
                        continue
                    try:
                        event = json.loads(raw)
                    except json.JSONDecodeError:
                        continue

                    usage = event.get("usageMetadata")
                    if usage:
                        prompt_tokens = usage.get("promptTokenCount", prompt_tokens)
                        output_tokens = usage.get("candidatesTokenCount", output_tokens)

                    for candidate in event.get("candidates", []):
                        for part in candidate.get("content", {}).get("parts", []):
                            if "text" in part:
                                yield LLMDelta(kind="text_delta", text=part["text"])
                            if "functionCall" in part:
                                fn = part["functionCall"]
                                fn_name = fn.get("name", "")
                                args = fn.get("args", {})
                                dedupe_key = f"{fn_name}:{json.dumps(args, sort_keys=True)}"
                                if dedupe_key in emitted_tool_calls:
                                    continue
                                emitted_tool_calls.add(dedupe_key)
                                yield LLMDelta(
                                    kind="tool_call",
                                    tool_call_id=str(uuid.uuid4()),
                                    tool_name=fn_name,
                                    tool_args_json=json.dumps(args),
                                )

        yield LLMDelta(
            kind="done",
            prompt_tokens=prompt_tokens,
            output_tokens=output_tokens,
        )
