from __future__ import annotations

import httpx
import pytest

from agents.orchestration.llm_errors import format_llm_error


def test_format_dns_error() -> None:
    exc = OSError(-3, "Temporary failure in name resolution")
    message = format_llm_error(exc)
    assert "Cannot reach LLM provider" in message
    assert "network" in message.lower()


def test_format_connect_error() -> None:
    message = format_llm_error(httpx.ConnectError("connection failed"))
    assert "Cannot reach LLM provider" in message
