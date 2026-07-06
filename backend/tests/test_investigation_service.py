"""Integration test for the InvestigationService orchestration.

Uses a fake executor that returns canned kubectl JSON so the full flow
(pods -> logs -> events -> deployments -> network) can be exercised without a
real cluster.
"""

import json

from app.kubernetes.executor import KubectlExecutor, KubectlResult
from app.services.investigation import InvestigationService

PODS = {
    "items": [
        {
            "metadata": {"name": "payment-service-1", "namespace": "shop"},
            "status": {
                "phase": "Running",
                "containerStatuses": [
                    {"state": {"waiting": {"reason": "CrashLoopBackOff", "message": "back-off"}},
                     "restartCount": 8}
                ],
            },
        },
        {
            "metadata": {"name": "web-1", "namespace": "shop"},
            "status": {"phase": "Running", "containerStatuses": [{"state": {"running": {}}, "restartCount": 0}]},
        },
    ]
}

EVENTS = {
    "items": [
        {"reason": "BackOff", "type": "Warning", "count": 12, "message": "Back-off restarting",
         "metadata": {"namespace": "shop"}, "involvedObject": {"kind": "Pod", "name": "payment-service-1"}}
    ]
}

DEPLOYMENTS = {
    "items": [
        {
            "metadata": {"name": "payment-service", "namespace": "shop"},
            "spec": {"replicas": 3},
            "status": {"availableReplicas": 0, "unavailableReplicas": 3, "readyReplicas": 0,
                       "conditions": [{"type": "Available", "status": "False", "reason": "MinimumReplicasUnavailable"}]},
        }
    ]
}

SERVICES = {"items": [{"metadata": {"name": "payment-service", "namespace": "shop"},
                        "spec": {"type": "ClusterIP", "selector": {"app": "payment"}}}]}
ENDPOINTS = {"items": [{"metadata": {"name": "payment-service", "namespace": "shop"}, "subsets": []}]}

LOGS = "Traceback (most recent call last):\npsycopg2.OperationalError: connection refused"


class FakeExecutor(KubectlExecutor):
    """Returns canned responses based on the kubectl subcommand."""

    def run(self, args):  # type: ignore[override]
        if args[:1] == ["version"]:
            return KubectlResult(command=args, success=True, returncode=0, stdout="{}")
        if args[:1] == ["logs"]:
            return KubectlResult(command=args, success=True, returncode=0, stdout=LOGS)
        mapping = {
            "pods": PODS, "events": EVENTS, "deployments": DEPLOYMENTS,
            "svc": SERVICES, "endpoints": ENDPOINTS,
        }
        resource = args[1] if len(args) > 1 else ""
        payload = mapping.get(resource, {"items": []})
        return KubectlResult(command=args, success=True, returncode=0, stdout=json.dumps(payload))


def test_full_investigation_flow():
    result = InvestigationService(executor=FakeExecutor()).run()

    assert result["meta"]["cluster_reachable"] is True
    assert result["meta"]["overall_healthy"] is False

    # Pods
    assert result["pods"]["problematic_count"] == 1
    assert result["pods"]["problematic_pods"][0]["status"] == "CrashLoopBackOff"

    # Logs collected for the failing pod, with categorized matches
    assert result["logs"]["inspected_pods"] == 1
    categories = {m["category"] for m in result["logs"]["pods"][0]["matched"]}
    assert "exception" in categories and "connection_failure" in categories

    # Events, deployments, network all flagged
    assert result["events"]["reason_counts"].get("BackOff") == 1
    assert result["deployments"]["unhealthy_count"] == 1
    assert result["network"]["problematic_count"] == 1
