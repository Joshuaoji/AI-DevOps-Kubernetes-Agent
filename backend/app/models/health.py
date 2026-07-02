"""Response models for the health endpoint."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Shape of the ``GET /health`` response."""

    status: str
    service: str
