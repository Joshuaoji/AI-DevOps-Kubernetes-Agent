"""OpenRouter LLM client.

A small, explainable HTTPX wrapper around the OpenRouter chat-completions API.
The API key is provisioned by InsForge (`insforge ai setup`) and read from the
environment - it is never logged or returned in responses.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import httpx

from app.core.config import Settings, get_settings
from app.core.logging import logger

# HTTP status codes that are worth retrying (rate limit + transient server errors).
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


@dataclass
class LLMResult:
    """Outcome of a chat-completion call."""

    success: bool
    content: str = ""
    error: str | None = None
    status_code: int | None = None
    model: str | None = None


class OpenRouterClient:
    """Calls OpenRouter chat completions with retries and graceful failures."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def chat(self, messages: list[dict[str, str]], *, temperature: float = 0.0) -> LLMResult:
        """Send a chat-completion request and return a structured result."""
        if not self.settings.openrouter_configured:
            return LLMResult(
                success=False,
                error="OPENROUTER_API_KEY is not configured. Run `insforge ai setup`.",
            )

        model = self.settings.resolved_model
        url = f"{self.settings.openrouter_base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.settings.openrouter_api_key}",
            "Content-Type": "application/json",
            # Optional attribution headers recommended by OpenRouter.
            "HTTP-Referer": "https://insforge.dev",
            "X-Title": "AI Kubernetes Agent",
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": self.settings.openrouter_max_tokens,
        }

        attempts = self.settings.openrouter_max_retries + 1
        last_error = "unknown error"

        for attempt in range(1, attempts + 1):
            try:
                with httpx.Client(timeout=self.settings.openrouter_timeout_seconds) as client:
                    response = client.post(url, json=payload, headers=headers)
            except httpx.TimeoutException:
                last_error = f"request timed out after {self.settings.openrouter_timeout_seconds}s"
                logger.warning("OpenRouter timeout (attempt {a}/{n})", a=attempt, n=attempts)
            except httpx.RequestError as exc:
                last_error = f"network error: {exc.__class__.__name__}"
                logger.warning("OpenRouter network error (attempt {a}/{n}): {e}", a=attempt, n=attempts, e=last_error)
            else:
                if response.status_code == 200:
                    content = self._extract_content(response)
                    if content is None:
                        return LLMResult(success=False, error="malformed OpenRouter response", model=model)
                    return LLMResult(success=True, content=content, status_code=200, model=model)

                last_error = f"OpenRouter returned HTTP {response.status_code}"
                logger.warning(
                    "OpenRouter HTTP {code} (attempt {a}/{n})",
                    code=response.status_code,
                    a=attempt,
                    n=attempts,
                )
                if response.status_code not in _RETRYABLE_STATUS:
                    return LLMResult(success=False, error=last_error, status_code=response.status_code, model=model)

            if attempt < attempts:
                time.sleep(min(2 ** (attempt - 1), 8))  # exponential backoff, capped

        return LLMResult(success=False, error=last_error, model=model)

    @staticmethod
    def _extract_content(response: httpx.Response) -> str | None:
        """Pull the assistant message text out of an OpenRouter response."""
        try:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError):
            return None
