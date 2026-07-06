"""Orchestrator entrypoint.

Thin wrapper around :class:`InvestigationService`. This is the seam where AI
reasoning will later consume the gathered evidence; for now it just runs the
investigation and returns the raw evidence payload.
"""

from __future__ import annotations

from typing import Any

from app.services.investigation import InvestigationService


def investigate_cluster() -> dict[str, Any]:
    """Run an on-demand investigation and return structured evidence."""
    return InvestigationService().run()
