"""Deployment inspector.

Runs ``kubectl get deployments -A -o json`` and flags deployments that are not
fully available (missing replicas, failed rollouts, bad conditions).
"""

from __future__ import annotations

from typing import Any

from app.kubernetes.executor import KubectlExecutor


def _bad_conditions(conditions: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Return deployment conditions that indicate trouble."""
    bad: list[dict[str, str]] = []
    for condition in conditions or []:
        ctype = condition.get("type")
        cstatus = condition.get("status")
        # Available should be True; Progressing False (or ProgressDeadlineExceeded) is bad.
        is_bad = (ctype == "Available" and cstatus != "True") or (
            ctype == "Progressing"
            and (cstatus == "False" or condition.get("reason") == "ProgressDeadlineExceeded")
        )
        if is_bad:
            bad.append(
                {
                    "type": ctype,
                    "status": cstatus,
                    "reason": condition.get("reason", ""),
                    "message": (condition.get("message") or "").strip()[:300],
                }
            )
    return bad


def analyze_deployments(deployments_json: dict[str, Any] | None) -> dict[str, Any]:
    """Summarize unhealthy deployments."""
    if not deployments_json:
        return {"healthy": True, "total_deployments": 0, "unhealthy_count": 0, "unhealthy_deployments": []}

    items = deployments_json.get("items", []) or []
    unhealthy: list[dict[str, Any]] = []

    for dep in items:
        metadata = dep.get("metadata", {}) or {}
        spec = dep.get("spec", {}) or {}
        status = dep.get("status", {}) or {}

        desired = spec.get("replicas", 0)
        available = status.get("availableReplicas", 0) or 0
        unavailable = status.get("unavailableReplicas", 0) or 0
        ready = status.get("readyReplicas", 0) or 0

        bad_conditions = _bad_conditions(status.get("conditions", []) or [])
        is_unhealthy = available < desired or unavailable > 0 or bool(bad_conditions)

        if not is_unhealthy:
            continue

        unhealthy.append(
            {
                "name": metadata.get("name", "<unknown>"),
                "namespace": metadata.get("namespace", "default"),
                "desired_replicas": desired,
                "available_replicas": available,
                "ready_replicas": ready,
                "unavailable_replicas": unavailable,
                "bad_conditions": bad_conditions,
            }
        )

    return {
        "healthy": len(unhealthy) == 0,
        "total_deployments": len(items),
        "unhealthy_count": len(unhealthy),
        "unhealthy_deployments": unhealthy,
    }


def inspect_deployments(executor: KubectlExecutor) -> dict[str, Any]:
    """Fetch deployments from the cluster and analyze them."""
    data, result = executor.get_json(["get", "deployments", "-A"])
    report = analyze_deployments(data)
    if not result.success:
        report["error"] = result.error
    return report
