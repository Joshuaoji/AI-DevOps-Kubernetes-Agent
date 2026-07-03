"""Response models for the investigation endpoint.

The evidence payload is deliberately flexible (dicts) so the Kubernetes layer
can evolve without breaking the API contract. The top-level shape is fixed.
"""

from typing import Any

from pydantic import BaseModel, Field


class Investigation(BaseModel):
    """Structured Kubernetes evidence gathered by the investigation layer."""

    meta: dict[str, Any] = Field(default_factory=dict)
    pods: dict[str, Any] = Field(default_factory=dict)
    logs: dict[str, Any] = Field(default_factory=dict)
    events: dict[str, Any] = Field(default_factory=dict)
    deployments: dict[str, Any] = Field(default_factory=dict)
    network: dict[str, Any] = Field(default_factory=dict)


class InvestigateResponse(BaseModel):
    """Envelope returned by ``POST /investigate``."""

    status: str
    investigation: Investigation
