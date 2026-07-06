"""Response model for the AI diagnosis produced from the investigation evidence."""

from typing import Any

from pydantic import BaseModel, Field


class Diagnosis(BaseModel):
    """Senior-SRE style diagnosis derived from the Kubernetes evidence.

    ``available`` is ``False`` when reasoning could not run (e.g. no OpenRouter
    key, unreachable cluster, or an LLM/parsing failure); ``error`` explains why.
    """

    available: bool = False
    root_cause: str | None = None
    explanation: str | None = None
    fix: str | None = None
    kubectl_command: str | None = None
    kubectl_commands: list[str] = Field(default_factory=list)
    prevention: str | None = None
    confidence: int | None = None
    confidence_reasoning: str | None = None
    model: str | None = None
    error: str | None = None

    @classmethod
    def unavailable(cls, error: str) -> "Diagnosis":
        """Build an 'AI could not run' diagnosis with a reason."""
        return cls(available=False, error=error)

    def model_dump_public(self) -> dict[str, Any]:
        """Serialize for the API response."""
        return self.model_dump()
