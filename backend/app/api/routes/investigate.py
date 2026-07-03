"""Investigation endpoint.

``POST /investigate`` runs the Kubernetes investigation layer and returns the
gathered evidence. No AI reasoning or root-cause analysis happens here yet.
"""

from fastapi import APIRouter

from app.models.investigation import Investigation, InvestigateResponse
from app.services.investigation import InvestigationService

router = APIRouter(tags=["investigation"])


@router.post("/investigate", response_model=InvestigateResponse)
def investigate() -> InvestigateResponse:
    """Collect structured Kubernetes troubleshooting evidence."""
    evidence = InvestigationService().run()
    return InvestigateResponse(status="success", investigation=Investigation(**evidence))
