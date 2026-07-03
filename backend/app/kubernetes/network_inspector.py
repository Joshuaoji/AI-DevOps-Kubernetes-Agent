"""Network inspector.

Inspects Services and their Endpoints to spot common networking problems:
services with no backing endpoints (selector matches nothing / no ready pods)
and potential DNS issues (the cluster DNS service having no endpoints).
"""

from __future__ import annotations

from typing import Any

from app.kubernetes.executor import KubectlExecutor

# Services we never flag (they legitimately have no selector/endpoints).
_IGNORED_SERVICES = {("default", "kubernetes")}
_DNS_SERVICES = {"kube-dns", "coredns"}


def _endpoint_index(endpoints_json: dict[str, Any] | None) -> dict[tuple[str, str], int]:
    """Map (namespace, name) -> count of ready endpoint addresses."""
    index: dict[tuple[str, str], int] = {}
    if not endpoints_json:
        return index
    for ep in endpoints_json.get("items", []) or []:
        metadata = ep.get("metadata", {}) or {}
        key = (metadata.get("namespace", "default"), metadata.get("name", ""))
        ready = 0
        for subset in ep.get("subsets", []) or []:
            ready += len(subset.get("addresses", []) or [])
        index[key] = index.get(key, 0) + ready
    return index


def analyze_network(
    services_json: dict[str, Any] | None,
    endpoints_json: dict[str, Any] | None,
) -> dict[str, Any]:
    """Summarize services with networking problems."""
    if not services_json:
        return {"healthy": True, "total_services": 0, "problematic_count": 0, "problematic_services": []}

    endpoints = _endpoint_index(endpoints_json)
    items = services_json.get("items", []) or []
    problematic: list[dict[str, Any]] = []

    for svc in items:
        metadata = svc.get("metadata", {}) or {}
        spec = svc.get("spec", {}) or {}
        name = metadata.get("name", "<unknown>")
        namespace = metadata.get("namespace", "default")
        svc_type = spec.get("type", "ClusterIP")
        selector = spec.get("selector") or {}

        if (namespace, name) in _IGNORED_SERVICES or svc_type == "ExternalName":
            continue

        ready_addresses = endpoints.get((namespace, name), 0)
        issue: str | None = None

        if selector and ready_addresses == 0:
            issue = "no ready endpoints (selector matches no ready pods / selector mismatch)"
        elif not selector and ready_addresses == 0:
            issue = "no endpoints (service has no selector and no manual endpoints)"

        if issue is None:
            continue

        entry = {
            "name": name,
            "namespace": namespace,
            "type": svc_type,
            "selector": selector,
            "ready_addresses": ready_addresses,
            "issue": issue,
        }
        if name in _DNS_SERVICES:
            entry["dns_warning"] = "cluster DNS service has no ready endpoints; DNS resolution may fail"
        problematic.append(entry)

    return {
        "healthy": len(problematic) == 0,
        "total_services": len(items),
        "problematic_count": len(problematic),
        "problematic_services": problematic,
    }


def inspect_network(executor: KubectlExecutor) -> dict[str, Any]:
    """Fetch services + endpoints from the cluster and analyze them."""
    services, svc_result = executor.get_json(["get", "svc", "-A"])
    endpoints, ep_result = executor.get_json(["get", "endpoints", "-A"])
    report = analyze_network(services, endpoints)
    errors = [r.error for r in (svc_result, ep_result) if not r.success]
    if errors:
        report["error"] = "; ".join(errors)
    return report
