"""Logs collector.

Fetches a small tail of logs for problematic pods and highlights lines that
look like real failures (exceptions, connection errors, missing config, image
or startup problems). Logs are kept intentionally concise - we never return
thousands of lines.
"""

from __future__ import annotations

from typing import Any

from app.kubernetes.executor import KubectlExecutor

# Ordered mapping of failure category -> substrings to look for (case-insensitive).
LOG_PATTERNS: dict[str, list[str]] = {
    "exception": ["exception", "traceback", "panic:", "fatal", "stacktrace", "unhandled"],
    "connection_failure": [
        "connection refused",
        "connection reset",
        "econnrefused",
        "no route to host",
        "could not connect",
        "dial tcp",
        "timed out",
        "timeout",
    ],
    "missing_env_var": [
        "environment variable",
        "env var",
        "is not set",
        "not defined",
        "missing required",
        "keyerror",
    ],
    "image_failure": [
        "imagepull",
        "errimagepull",
        "manifest unknown",
        "pull access denied",
        "no such image",
    ],
    "startup_error": [
        "failed to start",
        "exited with code",
        "cannot start",
        "startup probe failed",
        "error starting",
    ],
}

# Hard caps so responses stay small.
MAX_MATCHED_LINES = 15
MAX_TAIL_LINES_RETURNED = 20


def scan_logs(text: str) -> list[dict[str, str]]:
    """Return categorized matches for interesting lines in a log blob."""
    matches: list[dict[str, str]] = []
    seen: set[str] = set()

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        lowered = line.lower()
        for category, needles in LOG_PATTERNS.items():
            if any(needle in lowered for needle in needles):
                key = f"{category}:{line}"
                if key not in seen:
                    seen.add(key)
                    matches.append({"category": category, "line": line[:300]})
                break
        if len(matches) >= MAX_MATCHED_LINES:
            break
    return matches


def _fetch_pod_logs(
    executor: KubectlExecutor, name: str, namespace: str, tail: int
) -> tuple[str, str | None]:
    """Fetch logs for a pod, falling back to the previous container instance."""
    result = executor.run(
        ["logs", name, "-n", namespace, "--all-containers=true", f"--tail={tail}"]
    )
    if result.success and result.stdout.strip():
        return result.stdout, None

    # Crash-looping pods often have empty current logs; try the previous run.
    previous = executor.run(
        ["logs", name, "-n", namespace, "--all-containers=true", "--previous", f"--tail={tail}"]
    )
    if previous.success and previous.stdout.strip():
        return previous.stdout, None

    error = result.error or previous.error or "no logs available"
    return "", error


def collect_logs(
    executor: KubectlExecutor,
    problematic_pods: list[dict[str, Any]],
    tail: int = 50,
) -> dict[str, Any]:
    """Collect concise logs + matched failure lines for each problematic pod."""
    pods_report: list[dict[str, Any]] = []

    for pod in problematic_pods:
        name = pod.get("name")
        namespace = pod.get("namespace", "default")
        if not name:
            continue

        raw, error = _fetch_pod_logs(executor, name, namespace, tail)
        tail_lines = [ln for ln in raw.splitlines() if ln.strip()][-MAX_TAIL_LINES_RETURNED:]

        pods_report.append(
            {
                "name": name,
                "namespace": namespace,
                "matched": scan_logs(raw),
                "recent_lines": tail_lines,
                "error": error,
            }
        )

    return {"inspected_pods": len(pods_report), "pods": pods_report}
