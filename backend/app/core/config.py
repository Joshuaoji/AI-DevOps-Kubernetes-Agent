"""Application settings loaded from environment variables.

Uses pydantic-settings so values can come from a real environment or a local
``.env`` file. Only foundation-level settings live here; Kubernetes/AI specific
configuration will be added in later iterations.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Service metadata
    service_name: str = "ai-kubernetes-agent"
    environment: str = "development"

    # CORS: comma-separated list of allowed origins for the frontend.
    cors_origins: str = "http://localhost:3000"

    # AI reasoning (OpenRouter, key provisioned by InsForge `ai setup`).
    openrouter_api_key: str = ""
    openrouter_model: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_timeout_seconds: float = 45.0
    openrouter_max_retries: int = 2
    openrouter_max_tokens: int = 1500
    kubeconfig_path: str = ""

    @property
    def openrouter_configured(self) -> bool:
        """True when an OpenRouter API key is available."""
        return bool(self.openrouter_api_key.strip())

    @property
    def resolved_model(self) -> str:
        """Model to use, falling back to a sensible default when unset."""
        return self.openrouter_model.strip() or "openai/gpt-4o-mini"

    # Kubernetes investigation layer settings.
    kubectl_binary: str = "kubectl"
    kubectl_timeout_seconds: int = 30
    # Max log lines fetched per problematic pod (kept small on purpose).
    log_tail_lines: int = 50

    @property
    def cors_origins_list(self) -> list[str]:
        """Return CORS origins as a clean list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
