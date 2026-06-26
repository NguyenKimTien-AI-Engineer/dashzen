from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncGenerator

import httpx

from core.config import get_settings
from core.llm.thinking import (
    deltas_from_ollama_message,
    is_ollama_think_rejection,
    resolve_ollama_think_param,
)
from core.llm.types import LLMDelta, LLMMessage, ToolDefinition

log = logging.getLogger(__name__)

_CLOUD_HOST = "ollama.com"
_CLOUD_MAX_PREDICT = 8192
_RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})
_RETRYABLE_NETWORK = (
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
    httpx.PoolTimeout,
    OSError,
)
_MAX_RETRIES = 3


def _build_tools_payload(tools: list[ToolDefinition]) -> list[dict]:  # type: ignore[type-arg]
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


def _normalize_tool_calls(tool_calls: list[dict]) -> list[dict]:  # type: ignore[type-arg]
    normalized: list[dict] = []
    for tc in tool_calls:
        if "function" in tc:
            normalized.append(tc)
            continue
        args = tc.get("input") or tc.get("arguments") or {}
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                args = {}
        normalized.append({
            "function": {
                "name": tc.get("name", ""),
                "arguments": args if isinstance(args, dict) else {},
            }
        })
    return normalized


def _messages_to_ollama(messages: list[LLMMessage]) -> list[dict]:  # type: ignore[type-arg]
    result: list[dict] = []  # type: ignore[type-arg]
    for m in messages:
        if isinstance(m.content, list):
            content = " ".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in m.content
            )
        else:
            content = m.content or ""

        if m.role == "tool":
            result.append({"role": "tool", "content": content})
            continue

        role = m.role
        if role == "system" and result and result[-1]["role"] == "user":
            result[-1]["content"] = f"{content}\n\n{result[-1]['content']}"
            continue

        payload: dict = {"role": role, "content": content}  # type: ignore[type-arg]
        if m.tool_calls:
            payload["tool_calls"] = _normalize_tool_calls(m.tool_calls)
        result.append(payload)
    return result


class OllamaProvider:
    def __init__(self, base_url: str, model: str, *, api_key: str = "") -> None:
        self._base_url = base_url.rstrip("/")
        self._model = self._normalize_model(base_url, model)
        self._api_key = api_key
        self._is_cloud = _CLOUD_HOST in self._base_url

    @staticmethod
    def _normalize_model(base_url: str, model: str) -> str:
        if _CLOUD_HOST in base_url and model.endswith("-cloud"):
            return model[: -len("-cloud")]
        return model

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    def _cap_predict(self, max_tokens: int) -> int:
        if self._is_cloud:
            return min(max_tokens, _CLOUD_MAX_PREDICT)
        return max_tokens

    @staticmethod
    def _http_error_detail(resp: httpx.Response) -> str:
        try:
            body = resp.json()
            if isinstance(body, dict):
                return str(body.get("error") or body.get("message") or body)
        except Exception:
            pass
        text = resp.text.strip()
        return text[:300] if text else resp.reason_phrase

    async def _post_with_retry(
        self,
        client: httpx.AsyncClient,
        payload: dict,  # type: ignore[type-arg]
    ) -> httpx.Response:
        last_exc: httpx.HTTPStatusError | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                resp = await client.post(
                    f"{self._base_url}/api/chat",
                    headers=self._headers(),
                    json=payload,
                )
            except _RETRYABLE_NETWORK:
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(2**attempt)
                    continue
                raise
            if resp.status_code not in _RETRYABLE_STATUS:
                if resp.is_error:
                    detail = self._http_error_detail(resp)
                    raise httpx.HTTPStatusError(
                        f"Ollama API error {resp.status_code}: {detail}",
                        request=resp.request,
                        response=resp,
                    )
                return resp
            last_exc = httpx.HTTPStatusError(
                f"Ollama API error {resp.status_code}: {self._http_error_detail(resp)}",
                request=resp.request,
                response=resp,
            )
            if attempt < _MAX_RETRIES - 1:
                await asyncio.sleep(2**attempt)
        assert last_exc is not None
        raise last_exc

    async def chat(
        self,
        messages: list[LLMMessage],
        *,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> str:
        payload = {
            "model": self._model,
            "messages": _messages_to_ollama(messages),
            "stream": False,
            "options": {
                "num_predict": self._cap_predict(max_tokens),
                "temperature": temperature,
            },
        }
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await self._post_with_retry(client, payload)
            data = resp.json()
            return data.get("message", {}).get("content", "")

    async def _stream_once(
        self,
        payload: dict,  # type: ignore[type-arg]
    ) -> AsyncGenerator[LLMDelta, None]:
        async with httpx.AsyncClient(timeout=300) as client:
            async with client.stream(
                "POST",
                f"{self._base_url}/api/chat",
                headers=self._headers(),
                json=payload,
            ) as resp:
                if resp.is_error:
                    await resp.aread()
                    detail = self._http_error_detail(resp)
                    raise httpx.HTTPStatusError(
                        f"Ollama API error {resp.status_code}: {detail}",
                        request=resp.request,
                        response=resp,
                    )
                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    msg = data.get("message", {})
                    for delta in deltas_from_ollama_message(msg):
                        yield delta

                    if data.get("done"):
                        yield LLMDelta(
                            kind="done",
                            prompt_tokens=data.get("prompt_eval_count"),
                            output_tokens=data.get("eval_count"),
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
        settings = get_settings()
        think_param = resolve_ollama_think_param(
            enabled=thinking_enabled,
            level=settings.ollama_think_level,
            model=self._model,
        )

        payload: dict = {  # type: ignore[type-arg]
            "model": self._model,
            "messages": _messages_to_ollama(messages),
            "stream": True,
            "options": {
                "num_predict": self._cap_predict(max_tokens),
                "temperature": temperature,
            },
        }
        if tools:
            payload["tools"] = _build_tools_payload(tools)
        if think_param is not None:
            payload["think"] = think_param

        last_exc: httpx.HTTPStatusError | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                async for delta in self._stream_once(payload):
                    yield delta
                return
            except _RETRYABLE_NETWORK:
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(2**attempt)
                    continue
                raise
            except httpx.HTTPStatusError as exc:
                if think_param is not None and is_ollama_think_rejection(exc):
                    log.warning(
                        "Ollama rejected think parameter for model %s; retrying without think",
                        self._model,
                    )
                    payload.pop("think", None)
                    think_param = None
                    async for delta in self._stream_once(payload):
                        yield delta
                    return
                last_exc = exc
                if (
                    exc.response.status_code not in _RETRYABLE_STATUS
                    or attempt >= _MAX_RETRIES - 1
                ):
                    raise
                await asyncio.sleep(2**attempt)
        if last_exc:
            raise last_exc
