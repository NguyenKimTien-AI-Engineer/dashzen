from __future__ import annotations

import httpx
from core.config import get_settings

_NETWORK_ERRORS = (
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
    httpx.PoolTimeout,
    OSError,
)


def format_llm_error(exc: BaseException) -> str:
    settings = get_settings()

    if isinstance(exc, httpx.HTTPStatusError):
        if exc.response.status_code == 429:
            message = "LLM rate limit exceeded. Please wait a minute and try again."
            try:
                body = exc.response.json()
                provider_msg = body.get("error", {}).get("message")
                if provider_msg:
                    message = provider_msg
            except Exception:
                pass
            return message
        if exc.response.status_code >= 500:
            message = (
                f"LLM provider ({settings.llm_provider}) returned {exc.response.status_code}. "
                "Please retry in a moment."
            )
            if settings.llm_provider == "ollama" and "ollama.com" in settings.ollama_base_url:
                message += " Ollama Cloud can be unstable — try LLM_PROVIDER=gemini in .env."
            return message
        return f"LLM request failed: {exc}"

    if isinstance(exc, _NETWORK_ERRORS) or (
        isinstance(exc, OSError) and getattr(exc, "errno", None) in {-2, -3}
    ):
        message = (
            f"Cannot reach LLM provider ({settings.llm_provider}). "
            "Check your network connection and provider settings."
        )
        if settings.llm_provider == "ollama":
            message += f" Current OLLAMA_BASE_URL={settings.ollama_base_url}."
            if "ollama.com" in settings.ollama_base_url:
                message += " Try a local Ollama instance or switch LLM_PROVIDER=gemini."
        return message

    if "ValidationError" in type(exc).__name__:
        return f"Agent configuration error: {exc}"

    return f"Processing error: {exc}"
