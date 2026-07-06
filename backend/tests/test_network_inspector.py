"""Unit tests for the network inspector."""

from app.kubernetes.network_inspector import analyze_network


def _svc(name, namespace="default", svc_type="ClusterIP", selector=None):
    return {
        "metadata": {"name": name, "namespace": namespace},
        "spec": {"type": svc_type, "selector": selector or {}},
    }


def _endpoints(name, namespace="default", addresses=0):
    subsets = [{"addresses": [{"ip": f"10.0.0.{i}"} for i in range(addresses)]}] if addresses else []
    return {"metadata": {"name": name, "namespace": namespace}, "subsets": subsets}


def test_service_with_ready_endpoints_is_healthy():
    services = {"items": [_svc("web", selector={"app": "web"})]}
    endpoints = {"items": [_endpoints("web", addresses=2)]}
    report = analyze_network(services, endpoints)
    assert report["healthy"] is True


def test_detects_missing_endpoints():
    services = {"items": [_svc("api", selector={"app": "api"})]}
    endpoints = {"items": [_endpoints("api", addresses=0)]}
    report = analyze_network(services, endpoints)
    assert report["healthy"] is False
    assert report["problematic_services"][0]["name"] == "api"
    assert "no ready endpoints" in report["problematic_services"][0]["issue"]


def test_ignores_default_kubernetes_service():
    services = {"items": [_svc("kubernetes", selector=None)]}
    endpoints = {"items": []}
    report = analyze_network(services, endpoints)
    assert report["healthy"] is True


def test_flags_dns_service():
    services = {"items": [_svc("kube-dns", namespace="kube-system", selector={"k8s-app": "kube-dns"})]}
    endpoints = {"items": [_endpoints("kube-dns", namespace="kube-system", addresses=0)]}
    report = analyze_network(services, endpoints)
    assert report["problematic_services"][0].get("dns_warning")
