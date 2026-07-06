"""FastAPI application entrypoint.

Wires together configuration, logging, CORS, and the API routers. ``POST
/investigate`` gathers Kubernetes evidence and returns an AI (Senior SRE)
diagnosis derived from it.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, investigate
from app.core.config import get_settings
from app.core.logging import logger, setup_logging


def create_app() -> FastAPI:
    """Application factory that builds and configures the FastAPI instance."""
    setup_logging()
    settings = get_settings()

    app = FastAPI(
        title="AI Kubernetes Agent",
        description="On-demand AI Kubernetes troubleshooting agent (foundation).",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(investigate.router)

    @app.on_event("startup")
    async def _on_startup() -> None:
        logger.info(
            "Starting {service} (env={env})",
            service=settings.service_name,
            env=settings.environment,
        )

    @app.get("/")
    def root() -> dict[str, str]:
        """Friendly root pointing at the health check."""
        return {"service": settings.service_name, "docs": "/docs", "health": "/health"}

    return app


app = create_app()
