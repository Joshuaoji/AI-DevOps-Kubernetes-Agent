"""Convenience re-exports for the Kubernetes investigation layer.

The real logic lives in the dedicated inspector modules. This module keeps a
single, discoverable import surface for the investigation service.
"""

from app.kubernetes.deployment_inspector import inspect_deployments
from app.kubernetes.events_analyzer import inspect_events
from app.kubernetes.logs_collector import collect_logs
from app.kubernetes.network_inspector import inspect_network
from app.kubernetes.pod_inspector import inspect_pods

__all__ = [
    "inspect_pods",
    "collect_logs",
    "inspect_events",
    "inspect_deployments",
    "inspect_network",
]
