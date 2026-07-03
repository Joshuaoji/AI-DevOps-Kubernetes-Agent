"""Unit tests for the pod inspector parser."""

from app.kubernetes.pod_inspector import analyze_pods


def _pod(name, namespace="default", phase="Running", waiting=None, terminated=None, restarts=0):
    state: dict = {}
    if waiting:
        state["waiting"] = {"reason": waiting, "message": f"{waiting} message"}
    if terminated:
        state["terminated"] = {"reason": terminated, "message": f"{terminated} message"}
    return {
        "metadata": {"name": name, "namespace": namespace},
        "status": {
            "phase": phase,
            "containerStatuses": [{"state": state, "restartCount": restarts}],
        },
    }


def test_all_healthy():
    data = {"items": [_pod("web-1"), _pod("web-2")]}
    report = analyze_pods(data)
    assert report["healthy"] is True
    assert report["total_pods"] == 2
    assert report["problematic_pods"] == []


def test_detects_crashloop_and_imagepull():
    data = {
        "items": [
            _pod("payment", phase="Running", waiting="CrashLoopBackOff", restarts=7),
            _pod("api", phase="Pending", waiting="ImagePullBackOff"),
            _pod("web", phase="Running"),
        ]
    }
    report = analyze_pods(data)
    assert report["healthy"] is False
    assert report["problematic_count"] == 2
    statuses = {p["name"]: p["status"] for p in report["problematic_pods"]}
    assert statuses["payment"] == "CrashLoopBackOff"
    assert statuses["api"] == "ImagePullBackOff"
    payment = next(p for p in report["problematic_pods"] if p["name"] == "payment")
    assert payment["restart_count"] == 7


def test_detects_oomkilled_and_pending():
    data = {
        "items": [
            _pod("worker", phase="Running", terminated="OOMKilled"),
            _pod("scheduler", phase="Pending"),
        ]
    }
    report = analyze_pods(data)
    assert report["problematic_count"] == 2


def test_empty_input():
    report = analyze_pods(None)
    assert report["healthy"] is True
    assert report["total_pods"] == 0
