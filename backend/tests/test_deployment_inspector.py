"""Unit tests for the deployment inspector."""

from app.kubernetes.deployment_inspector import analyze_deployments


def _deployment(name, desired=1, available=1, unavailable=0, conditions=None):
    return {
        "metadata": {"name": name, "namespace": "default"},
        "spec": {"replicas": desired},
        "status": {
            "availableReplicas": available,
            "unavailableReplicas": unavailable,
            "readyReplicas": available,
            "conditions": conditions or [],
        },
    }


def test_healthy_deployment():
    data = {"items": [_deployment("web", desired=3, available=3)]}
    report = analyze_deployments(data)
    assert report["healthy"] is True
    assert report["unhealthy_count"] == 0


def test_detects_missing_replicas():
    data = {"items": [_deployment("api", desired=3, available=1, unavailable=2)]}
    report = analyze_deployments(data)
    assert report["healthy"] is False
    entry = report["unhealthy_deployments"][0]
    assert entry["available_replicas"] == 1
    assert entry["unavailable_replicas"] == 2


def test_detects_progress_deadline_exceeded():
    conditions = [
        {"type": "Available", "status": "False", "reason": "MinimumReplicasUnavailable"},
        {"type": "Progressing", "status": "False", "reason": "ProgressDeadlineExceeded",
         "message": "exceeded its progress deadline"},
    ]
    data = {"items": [_deployment("payment", desired=1, available=1, conditions=conditions)]}
    report = analyze_deployments(data)
    assert report["unhealthy_count"] == 1
    assert len(report["unhealthy_deployments"][0]["bad_conditions"]) == 2
