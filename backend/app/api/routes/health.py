"""Health check endpoint."""

from fastapi import APIRouter

from app.core.config import get_settings
from app.models.health import HealthResponse

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return a simple liveness signal for the service."""
    settings = get_settings()
    return HealthResponse(status="healthy", service=settings.service_name)
