from core.config import get_settings
from core.llm.client import LLMClient
from core.llm.providers.anthropic import AnthropicProvider
from core.llm.providers.gemini import GeminiProvider
from core.llm.providers.ollama import OllamaProvider
from core.llm.providers.openai import OpenAIProvider
from core.llm.providers.openrouter import OpenRouterProvider


def get_llm_client() -> LLMClient:
    settings = get_settings()
    provider = settings.llm_provider
    if provider == "anthropic":
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic")
        return AnthropicProvider(settings.anthropic_api_key, settings.anthropic_model)  # type: ignore[return-value]
    if provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        return OpenAIProvider(settings.openai_api_key, settings.openai_model)  # type: ignore[return-value]
    if provider == "gemini":
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini")
        return GeminiProvider(settings.gemini_api_key, settings.gemini_model)  # type: ignore[return-value]
    if provider == "openrouter":
        if not settings.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY is required when LLM_PROVIDER=openrouter")
        return OpenRouterProvider(
            settings.openrouter_api_key,
            settings.openrouter_model,
            site_url=settings.openrouter_site_url,
            app_name=settings.openrouter_app_name,
        )  # type: ignore[return-value]
    return OllamaProvider(
        settings.ollama_base_url,
        settings.ollama_model,
        api_key=settings.ollama_api_key,
    )  # type: ignore[return-value]
