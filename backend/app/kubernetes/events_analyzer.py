"""Events analyzer.

Runs ``kubectl get events -A -o json`` and summarizes the warning-style events
that matter for troubleshooting.
"""

from __future__ import annotations

from typing import Any

from app.kubernetes.executor import KubectlExecutor

# Event reasons worth surfacing during an investigation.
INTERESTING_REASONS = {
    "FailedScheduling",
    "BackOff",
    "FailedMount",
    "FailedAttachVolume",
    "FailedPull",
    "ErrImagePull",
    "ImagePullBackOff",
    "Unhealthy",
    "FailedCreatePodSandBox",
    "NetworkNotReady",
    "FailedKillPod",
}

MAX_EVENTS_RETURNED = 25


def _involved(event: dict[str, Any]) -> str:
    obj = event.get("involvedObject", {}) or {}
    kind = obj.get("kind", "")
    name = obj.get("name", "")
    return f"{kind}/{name}".strip("/")


def analyze_events(events_json: dict[str, Any] | None) -> dict[str, Any]:
    """Summarize interesting Kubernetes events."""
    if not events_json:
        return {"total_interesting": 0, "reason_counts": {}, "events": []}

    items = events_json.get("items", []) or []
    findings: list[dict[str, Any]] = []
    reason_counts: dict[str, int] = {}

    for event in items:
        reason = event.get("reason", "")
        event_type = event.get("type", "")
        is_interesting = reason in INTERESTING_REASONS or event_type == "Warning"
        if not is_interesting:
            continue

        reason_counts[reason] = reason_counts.get(reason, 0) + 1
        metadata = event.get("metadata", {}) or {}
        findings.append(
            {
                "reason": reason,
                "type": event_type,
                "object": _involved(event),
                "namespace": metadata.get("namespace", "default"),
                "count": event.get("count", 1),
                "message": (event.get("message") or "").strip()[:300],
            }
        )

    # Most frequent / recent first (by count) and cap the list.
    findings.sort(key=lambda item: item.get("count", 1), reverse=True)

    return {
        "total_interesting": len(findings),
        "reason_counts": reason_counts,
        "events": findings[:MAX_EVENTS_RETURNED],
    }


def inspect_events(executor: KubectlExecutor) -> dict[str, Any]:
    """Fetch events from the cluster and analyze them."""
    data, result = executor.get_json(["get", "events", "-A"])
    report = analyze_events(data)
    if not result.success:
        report["error"] = result.error
    return report
