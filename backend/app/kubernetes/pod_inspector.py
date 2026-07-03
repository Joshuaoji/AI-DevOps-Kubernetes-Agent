"""Pod inspector.

Runs ``kubectl get pods -A -o json`` and turns the raw output into a concise
report of unhealthy pods. Parsing is split into a pure ``analyze_pods`` function
so it can be unit-tested without a cluster.
"""

from __future__ import annotations

from typing import Any

from app.kubernetes.executor import KubectlExecutor

# Container "waiting" reasons that indicate a problem.
PROBLEM_WAITING_REASONS = {
    "CrashLoopBackOff",
    "ImagePullBackOff",
    "ErrImagePull",
    "CreateContainerConfigError",
    "CreateContainerError",
    "InvalidImageName",
    "ContainerCreating",  # treated as suspicious (possibly stuck)
}

# Container "terminated" reasons that indicate a problem.
PROBLEM_TERMINATED_REASONS = {
    "OOMKilled",
    "Error",
    "ContainerCannotRun",
    "DeadlineExceeded",
}

# Pod phases that indicate a problem.
PROBLEM_PHASES = {"Pending", "Failed", "Unknown"}


def _container_problem(container_statuses: list[dict[str, Any]]) -> tuple[str | None, str | None]:
    """Return (reason, message) for the first problematic container, if any."""
    for status in container_statuses or []:
        state = status.get("state", {}) or {}
        waiting = state.get("waiting")
        if waiting and waiting.get("reason") in PROBLEM_WAITING_REASONS:
            return waiting.get("reason"), waiting.get("message")
        terminated = state.get("terminated")
        if terminated and terminated.get("reason") in PROBLEM_TERMINATED_REASONS:
            return terminated.get("reason"), terminated.get("message")
    return None, None


def _total_restarts(container_statuses: list[dict[str, Any]]) -> int:
    return sum(int(s.get("restartCount", 0)) for s in container_statuses or [])


def analyze_pods(pods_json: dict[str, Any] | None) -> dict[str, Any]:
    """Analyze ``kubectl get pods`` JSON and summarize unhealthy pods."""
    if not pods_json:
        return {"healthy": True, "total_pods": 0, "problematic_count": 0, "problematic_pods": []}

    items = pods_json.get("items", []) or []
    problematic: list[dict[str, Any]] = []

    for pod in items:
        metadata = pod.get("metadata", {}) or {}
        status = pod.get("status", {}) or {}
        name = metadata.get("name", "<unknown>")
        namespace = metadata.get("namespace", "default")
        phase = status.get("phase", "Unknown")

        container_statuses = list(status.get("containerStatuses", []) or [])
        container_statuses += list(status.get("initContainerStatuses", []) or [])

        reason, message = _container_problem(container_statuses)
        restart_count = _total_restarts(container_statuses)

        is_problem = reason is not None or phase in PROBLEM_PHASES
        if not is_problem:
            continue

        problematic.append(
            {
                "name": name,
                "namespace": namespace,
                "status": reason or phase,
                "phase": phase,
                "reason": reason,
                "restart_count": restart_count,
                "message": (message or "").strip() or None,
            }
        )

    return {
        "healthy": len(problematic) == 0,
        "total_pods": len(items),
        "problematic_count": len(problematic),
        "problematic_pods": problematic,
    }


def inspect_pods(executor: KubectlExecutor) -> dict[str, Any]:
    """Fetch pods from the cluster and analyze them."""
    data, result = executor.get_json(["get", "pods", "-A"])
    report = analyze_pods(data)
    if not result.success:
        report["error"] = result.error
    return report
