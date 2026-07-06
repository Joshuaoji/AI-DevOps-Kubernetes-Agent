"""Investigation endpoint.

``POST /investigate`` runs the Kubernetes investigation layer to gather evidence,
then sends that evidence to the AI Kubernetes agent for Senior-SRE style
reasoning (root cause, fix, confidence). The response includes both the raw
evidence and the diagnosis.
"""

from fastapi import APIRouter

from app.ai.agent import AIKubernetesAgent
from app.models.investigation import Investigation, InvestigateResponse
from app.services.investigation import InvestigationService

router = APIRouter(tags=["investigation"])


@router.post("/investigate", response_model=InvestigateResponse)
def investigate() -> InvestigateResponse:
    """Collect Kubernetes evidence and return an AI diagnosis."""
    evidence = InvestigationService().run()
    diagnosis = AIKubernetesAgent().diagnose(evidence)
    return InvestigateResponse(
        status="success",
        investigation=Investigation(**evidence),
        diagnosis=diagnosis,
    )
