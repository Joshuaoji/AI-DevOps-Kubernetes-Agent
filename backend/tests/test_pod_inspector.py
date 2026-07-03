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


def _pod_with_probes(name, *, liveness=False, readiness=False, running=True, ready=True,
                     restarts=0, last_terminated=None, namespace="default"):
    container_spec = {"name": "app"}
    if liveness:
        container_spec["livenessProbe"] = {"httpGet": {"path": "/healthz", "port": 8080}}
    if readiness:
        container_spec["readinessProbe"] = {"httpGet": {"path": "/ready", "port": 8080}}

    state = {"running": {"startedAt": "2026-07-03T20:00:00Z"}} if running else {}
    container_status = {"name": "app", "ready": ready, "restartCount": restarts, "state": state}
    if last_terminated:
        container_status["lastState"] = {"terminated": last_terminated}

    return {
        "metadata": {"name": name, "namespace": namespace},
        "spec": {"containers": [container_spec]},
        "status": {"phase": "Running", "containerStatuses": [container_status]},
    }


def test_detects_readiness_probe_failure():
    data = {"items": [_pod_with_probes("api", readiness=True, running=True, ready=False)]}
    report = analyze_pods(data)
    assert report["healthy"] is False
    pod = report["problematic_pods"][0]
    assert pod["status"] == "NotReady"
    assert any(i["type"] == "readiness" for i in pod["probe_issues"])


def test_detects_liveness_probe_restart():
    data = {
        "items": [
            _pod_with_probes(
                "worker", liveness=True, running=True, ready=True, restarts=5,
                last_terminated={"exitCode": 137, "reason": "Error"},
            )
        ]
    }
    report = analyze_pods(data)
    assert report["problematic_count"] == 1
    pod = report["problematic_pods"][0]
    liveness = [i for i in pod["probe_issues"] if i["type"] == "liveness"]
    assert liveness and "restarts=5" in liveness[0]["detail"]


def test_ready_pod_with_probes_is_healthy():
    data = {"items": [_pod_with_probes("web", liveness=True, readiness=True, ready=True)]}
    report = analyze_pods(data)
    assert report["healthy"] is True


def test_no_probe_defined_does_not_flag_readiness():
    # Not ready but no readiness probe defined -> not attributed to a probe.
    data = {"items": [_pod_with_probes("job", readiness=False, running=True, ready=False)]}
    report = analyze_pods(data)
    assert report["healthy"] is True
