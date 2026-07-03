"""Pod inspector.

Runs ``kubectl get pods -A -o json`` and turns the raw output into a concise
report of unhealthy pods, including likely liveness/readiness probe failures.
Parsing is split into a pure ``analyze_pods`` function so it can be unit-tested
without a cluster.
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


def _probe_definitions(pod_spec: dict[str, Any]) -> dict[str, dict[str, bool]]:
    """Map container name -> which probes (liveness/readiness) it defines."""
    definitions: dict[str, dict[str, bool]] = {}
    containers = list(pod_spec.get("containers", []) or [])
    containers += list(pod_spec.get("initContainers", []) or [])
    for container in containers:
        definitions[container.get("name")] = {
            "liveness": bool(container.get("livenessProbe")),
            "readiness": bool(container.get("readinessProbe")),
        }
    return definitions


def _probe_issues(
    container_statuses: list[dict[str, Any]],
    probe_defs: dict[str, dict[str, bool]],
) -> list[dict[str, Any]]:
    """Detect likely liveness/readiness probe failures from container status.

    - Readiness: a running container that is not ``Ready`` while it defines a
      readiness probe (the probe is failing so traffic is withheld).
    - Liveness: a container that defines a liveness probe and has been restarted
      after a termination (the failing probe is killing/restarting it).
    """
    issues: list[dict[str, Any]] = []
    for status in container_statuses or []:
        name = status.get("name")
        defs = probe_defs.get(name, {})
        state = status.get("state", {}) or {}
        running = "running" in state
        ready = bool(status.get("ready", False))
        restart_count = int(status.get("restartCount", 0))
        last_terminated = (status.get("lastState", {}) or {}).get("terminated")

        if defs.get("readiness") and running and not ready:
            issues.append(
                {
                    "type": "readiness",
                    "container": name,
                    "detail": "readiness probe failing (container running but not Ready)",
                }
            )

        if defs.get("liveness") and restart_count > 0 and last_terminated:
            issues.append(
                {
                    "type": "liveness",
                    "container": name,
                    "detail": (
                        "liveness probe likely restarting the container "
                        f"(restarts={restart_count}, "
                        f"lastExitCode={last_terminated.get('exitCode')}, "
                        f"reason={last_terminated.get('reason')})"
                    ),
                }
            )
    return issues


def analyze_pods(pods_json: dict[str, Any] | None) -> dict[str, Any]:
    """Analyze ``kubectl get pods`` JSON and summarize unhealthy pods."""
    if not pods_json:
        return {"healthy": True, "total_pods": 0, "problematic_count": 0, "problematic_pods": []}

    items = pods_json.get("items", []) or []
    problematic: list[dict[str, Any]] = []

    for pod in items:
        metadata = pod.get("metadata", {}) or {}
        status = pod.get("status", {}) or {}
        spec = pod.get("spec", {}) or {}
        name = metadata.get("name", "<unknown>")
        namespace = metadata.get("namespace", "default")
        phase = status.get("phase", "Unknown")

        container_statuses = list(status.get("containerStatuses", []) or [])
        container_statuses += list(status.get("initContainerStatuses", []) or [])

        reason, message = _container_problem(container_statuses)
        restart_count = _total_restarts(container_statuses)
        probe_issues = _probe_issues(container_statuses, _probe_definitions(spec))

        is_problem = reason is not None or phase in PROBLEM_PHASES or bool(probe_issues)
        if not is_problem:
            continue

        # Prefer an explicit container reason; otherwise a bad phase; otherwise
        # surface probe failures as a "NotReady" status.
        if reason:
            status_label = reason
        elif phase in PROBLEM_PHASES:
            status_label = phase
        else:
            status_label = "NotReady"

        problematic.append(
            {
                "name": name,
                "namespace": namespace,
                "status": status_label,
                "phase": phase,
                "reason": reason,
                "restart_count": restart_count,
                "message": (message or "").strip() or None,
                "probe_issues": probe_issues,
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
