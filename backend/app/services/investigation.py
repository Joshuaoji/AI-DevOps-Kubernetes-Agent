"""Investigation service.

Orchestrates the Kubernetes investigation layer. It behaves like a junior
DevOps engineer collecting evidence: check pods, collect logs for the failing
ones, analyze events, inspect deployments, and check networking - then return a
single structured payload. No AI reasoning happens here.
"""

from __future__ import annotations

from typing import Any

from app.core.config import get_settings
from app.core.logging import logger
from app.kubernetes.deployment_inspector import inspect_deployments
from app.kubernetes.events_analyzer import inspect_events
from app.kubernetes.executor import KubectlExecutor
from app.kubernetes.logs_collector import collect_logs
from app.kubernetes.network_inspector import inspect_network
from app.kubernetes.pod_inspector import inspect_pods


class InvestigationService:
    """Runs the full evidence-gathering flow using kubectl."""

    def __init__(self, executor: KubectlExecutor | None = None) -> None:
        self.executor = executor or KubectlExecutor()
        self.settings = get_settings()

    def _cluster_reachable(self) -> tuple[bool, str | None]:
        """Cheap connectivity probe so we can report cluster reachability."""
        result = self.executor.run(["version", "--output=json"])
        if result.success:
            return True, None
        return False, result.error

    def run(self) -> dict[str, Any]:
        """Execute the investigation flow and return structured evidence."""
        logger.info("Starting Kubernetes investigation")
        reachable, reach_error = self._cluster_reachable()

        # 1. Check pods
        pods = inspect_pods(self.executor)

        # 2. Collect logs for the problematic pods only
        logs = collect_logs(
            self.executor,
            pods.get("problematic_pods", []),
            tail=self.settings.log_tail_lines,
        )

        # 3. Analyze events
        events = inspect_events(self.executor)

        # 4. Inspect deployments
        deployments = inspect_deployments(self.executor)

        # 5. Check networking
        network = inspect_network(self.executor)

        overall_healthy = bool(
            pods.get("healthy", True)
            and deployments.get("healthy", True)
            and network.get("healthy", True)
        )

        logger.info(
            "Investigation complete (reachable={reachable}, healthy={healthy})",
            reachable=reachable,
            healthy=overall_healthy,
        )

        return {
            "meta": {
                "cluster_reachable": reachable,
                "error": reach_error,
                "overall_healthy": overall_healthy if reachable else None,
            },
            "pods": pods,
            "logs": logs,
            "events": events,
            "deployments": deployments,
            "network": network,
        }
