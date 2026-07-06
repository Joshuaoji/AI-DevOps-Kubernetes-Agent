"""Unit tests for the OpenRouter client's guardrails (no network calls)."""

from app.ai.llm_client import OpenRouterClient
from app.core.config import Settings


def test_chat_without_api_key_fails_gracefully():
    # Explicitly force an empty key regardless of any .env on disk.
    settings = Settings(openrouter_api_key="", openrouter_model="test/model")
    client = OpenRouterClient(settings=settings)

    result = client.chat([{"role": "user", "content": "hi"}])

    assert result.success is False
    assert result.error is not None
    assert "OPENROUTER_API_KEY" in result.error


def test_resolved_model_falls_back_when_unset():
    assert Settings(openrouter_model="").resolved_model == "openai/gpt-4o-mini"
    assert Settings(openrouter_model="foo/bar").resolved_model == "foo/bar"
