"""Unit tests for the events analyzer."""

from app.kubernetes.events_analyzer import analyze_events


def _event(reason, etype="Warning", name="pod-x", namespace="default", count=1, message="msg"):
    return {
        "reason": reason,
        "type": etype,
        "count": count,
        "message": message,
        "metadata": {"namespace": namespace},
        "involvedObject": {"kind": "Pod", "name": name},
    }


def test_summarizes_interesting_events():
    data = {
        "items": [
            _event("FailedScheduling", count=3),
            _event("ErrImagePull", name="api", count=5),
            _event("Started", etype="Normal"),
        ]
    }
    report = analyze_events(data)
    assert report["total_interesting"] == 2
    assert report["reason_counts"]["FailedScheduling"] == 1
    # Sorted by count desc -> ErrImagePull (5) first.
    assert report["events"][0]["reason"] == "ErrImagePull"


def test_ignores_normal_events():
    data = {"items": [_event("Scheduled", etype="Normal")]}
    report = analyze_events(data)
    assert report["total_interesting"] == 0


def test_empty_input():
    assert analyze_events(None)["total_interesting"] == 0
