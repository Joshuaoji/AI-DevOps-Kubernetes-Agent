"""Unit tests for the AI prompt builder."""

from app.ai.prompt_builder import SYSTEM_PROMPT, build_messages, summarize_evidence

INVESTIGATION = {
    "meta": {"cluster_reachable": True, "overall_healthy": False},
    "pods": {"healthy": False, "total_pods": 3,
             "problematic_pods": [{"name": "payment-1", "status": "CrashLoopBackOff"}]},
    "logs": {"pods": [{"name": "payment-1", "matched": [{"category": "missing_env_var", "line": "DATABASE_URL not set"}]}]},
    "events": {"reason_counts": {"BackOff": 5}, "events": [{"reason": "BackOff"}]},
    "deployments": {"healthy": False, "unhealthy_deployments": [{"name": "payment"}]},
    "network": {"healthy": True, "problematic_services": []},
}


def test_system_prompt_is_senior_sre():
    assert "Senior Kubernetes" in SYSTEM_PROMPT
    # Must instruct a strict JSON contract with the required keys.
    for key in ["root_cause", "suggested_fix", "kubectl_commands", "confidence"]:
        assert key in SYSTEM_PROMPT


def test_summary_contains_all_sections():
    summary = summarize_evidence(INVESTIGATION)
    for heading in ["Pod Status", "Logs", "Events", "Deployment Health", "Networking Findings"]:
        assert heading in summary
    # Real evidence values should be embedded.
    assert "CrashLoopBackOff" in summary
    assert "DATABASE_URL not set" in summary


def test_build_messages_shape():
    messages = build_messages(INVESTIGATION)
    assert [m["role"] for m in messages] == ["system", "user"]
    assert messages[0]["content"] == SYSTEM_PROMPT
    assert "Pod Status" in messages[1]["content"]
