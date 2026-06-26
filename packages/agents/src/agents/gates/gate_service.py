from __future__ import annotations

import asyncio
import random
from typing import Literal

import redis.asyncio as aioredis
from core.config import get_settings

from agents.orchestration.constants import (
    GATE_TTL_SEC,
    MAX_CONSECUTIVE_ERRORS,
    POLL_INTERVAL_MS,
)

_GATE_PREFIX = "gate:"
_ASK_PREFIX = "ask:"

_mem_gates: dict[str, str] = {}
_mem_ask: dict[str, str] = {}

_SET_IF_PENDING = """
if redis.call("GET", KEYS[1]) == "pending" then
    return redis.call("SET", KEYS[1], ARGV[1], "EX", ARGV[2])
end
return nil
"""


async def _get_redis() -> aioredis.Redis | None:  # type: ignore[type-arg]
    try:
        r = aioredis.from_url(get_settings().redis_url, decode_responses=True)
        await r.ping()
        return r
    except Exception:
        return None


def _gate_key(task_id: str, call_id: str) -> str:
    return f"{_GATE_PREFIX}{task_id}:{call_id}"


def _ask_key(task_id: str, call_id: str) -> str:
    return f"{_ASK_PREFIX}{task_id}:{call_id}"


def _encode_decision(decision: str, feedback: str = "") -> str:
    if feedback:
        return f"{decision}_with:{feedback}"
    return decision


def _decode_gate_value(value: str) -> tuple[bool, str]:
    if value == "approved":
        return True, ""
    if value == "rejected":
        return False, ""
    if value.startswith("approved_with:"):
        return True, value[len("approved_with:") :]
    if value.startswith("rejected_with:"):
        return False, value[len("rejected_with:") :]
    return False, ""


async def init_gate(task_id: str, call_id: str) -> None:
    key = _gate_key(task_id, call_id)
    redis = await _get_redis()
    if redis is not None:
        try:
            await redis.set(key, "pending", nx=True, ex=GATE_TTL_SEC)
        finally:
            await redis.aclose()
    else:
        _mem_gates.setdefault(key, "pending")


async def resolve_gate(
    task_id: str,
    call_id: str,
    decision: Literal["approved", "rejected"],
    feedback: str = "",
) -> bool:
    key = _gate_key(task_id, call_id)
    value = _encode_decision(decision, feedback)
    redis = await _get_redis()
    if redis is not None:
        try:
            result = await redis.eval(  # type: ignore[attr-defined]
                _SET_IF_PENDING, 1, key, value, str(GATE_TTL_SEC)
            )
            return result is not None
        finally:
            await redis.aclose()
    current = _mem_gates.get(key)
    if current == "pending":
        _mem_gates[key] = value
        return True
    return False


async def register_gate(task_id: str, call_id: str) -> tuple[bool, str]:
    key = _gate_key(task_id, call_id)
    consecutive_errors = 0

    while True:
        redis = await _get_redis()
        if redis is not None:
            try:
                value = await redis.get(key)
                consecutive_errors = 0
            except Exception:
                consecutive_errors += 1
                if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                    return False, ""
                value = None
            finally:
                await redis.aclose()
        else:
            value = _mem_gates.get(key)

        if value is None:
            return False, ""
        if value == "pending":
            jitter_ms = POLL_INTERVAL_MS + random.randint(0, 99)
            await asyncio.sleep(jitter_ms / 1000.0)
            continue
        return _decode_gate_value(value)


async def init_ask_gate(task_id: str, call_id: str) -> None:
    key = _ask_key(task_id, call_id)
    redis = await _get_redis()
    if redis is not None:
        try:
            await redis.set(key, "pending", nx=True, ex=GATE_TTL_SEC)
        finally:
            await redis.aclose()
    else:
        _mem_ask.setdefault(key, "pending")


async def resolve_ask_gate(task_id: str, call_id: str, answer: str) -> bool:
    key = _ask_key(task_id, call_id)
    redis = await _get_redis()
    if redis is not None:
        try:
            result = await redis.eval(  # type: ignore[attr-defined]
                _SET_IF_PENDING, 1, key, answer, str(GATE_TTL_SEC)
            )
            return result is not None
        finally:
            await redis.aclose()
    current = _mem_ask.get(key)
    if current == "pending":
        _mem_ask[key] = answer
        return True
    return False


async def register_ask_gate(task_id: str, call_id: str) -> str:
    key = _ask_key(task_id, call_id)
    consecutive_errors = 0

    while True:
        redis = await _get_redis()
        if redis is not None:
            try:
                value = await redis.get(key)
                consecutive_errors = 0
            except Exception:
                consecutive_errors += 1
                if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                    return ""
                value = None
            finally:
                await redis.aclose()
        else:
            value = _mem_ask.get(key)

        if value is None:
            return ""
        if value == "pending":
            jitter_ms = POLL_INTERVAL_MS + random.randint(0, 99)
            await asyncio.sleep(jitter_ms / 1000.0)
            continue
        return value


async def unregister_all_gates(task_id: str) -> None:
    gate_pattern = f"{_GATE_PREFIX}{task_id}:*"
    ask_pattern = f"{_ASK_PREFIX}{task_id}:*"

    redis = await _get_redis()
    if redis is not None:
        try:
            for pattern in (gate_pattern, ask_pattern):
                cursor = 0
                while True:
                    cursor, keys = await redis.scan(cursor=cursor, match=pattern, count=100)
                    if keys:
                        await redis.delete(*keys)
                    if cursor == 0:
                        break
        finally:
            await redis.aclose()

    gate_prefix = f"{_GATE_PREFIX}{task_id}:"
    ask_prefix = f"{_ASK_PREFIX}{task_id}:"
    for k in list(_mem_gates):
        if k.startswith(gate_prefix):
            _mem_gates.pop(k, None)
    for k in list(_mem_ask):
        if k.startswith(ask_prefix):
            _mem_ask.pop(k, None)
