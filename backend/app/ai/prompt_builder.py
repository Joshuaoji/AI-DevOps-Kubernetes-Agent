"""Prompt builder for the AI Kubernetes agent.

Turns the structured investigation evidence into a deterministic troubleshooting
prompt that makes the LLM behave like a Senior Kubernetes SRE and answer with a
strict JSON object.
"""

from __future__ import annotations

import json
from typing import Any

SYSTEM_PROMPT = """You are a Senior Kubernetes Site Reliability Engineer (SRE) \
with deep production troubleshooting experience.

You are given structured evidence collected from a cluster: pod status, container \
logs, Kubernetes events, deployment health, and networking findings. Your job is to \
CORRELATE this evidence (do not just summarize the logs), determine the single most \
likely ROOT CAUSE, and give a practical, Kubernetes-specific fix.

Rules:
- Base every conclusion on the provided evidence. Do not invent pods, images, or errors.
- Be specific and actionable. Avoid vague advice like "check the logs".
- kubectl commands must be concrete and reference the real namespaces/resources in the evidence.
- The confidence score (0-100 integer) must reflect how strongly the evidence supports the root cause.
- If the evidence is insufficient, say so in the explanation and lower the confidence.

Respond with ONLY a single JSON object (no markdown, no prose) using exactly these keys:
{
  "root_cause": "one concise sentence naming the underlying cause",
  "explanation": "2-4 sentences correlating pods + logs + events + deployment/network state",
  "suggested_fix": "the concrete fix to apply",
  "kubectl_commands": ["kubectl ...", "kubectl ..."],
  "prevention": "how to prevent this class of failure in the future",
  "confidence": 0-100,
  "confidence_reasoning": "why this confidence level, citing specific evidence"
}"""


def _section(title: str, payload: Any) -> str:
    """Render one evidence section as compact JSON under a heading."""
    return f"## {title}\n{json.dumps(payload, indent=2, default=str)}"


def summarize_evidence(investigation: dict[str, Any]) -> str:
    """Build a focused, human-readable evidence summary for the user prompt."""
    pods = investigation.get("pods", {}) or {}
    logs = investigation.get("logs", {}) or {}
    events = investigation.get("events", {}) or {}
    deployments = investigation.get("deployments", {}) or {}
    network = investigation.get("network", {}) or {}

    sections = [
        _section(
            "Pod Status",
            {
                "healthy": pods.get("healthy"),
                "total_pods": pods.get("total_pods"),
                "problematic_pods": pods.get("problematic_pods", []),
            },
        ),
        _section("Logs (matched failure lines)", logs.get("pods", [])),
        _section(
            "Events",
            {
                "reason_counts": events.get("reason_counts", {}),
                "events": events.get("events", []),
            },
        ),
        _section(
            "Deployment Health",
            {
                "healthy": deployments.get("healthy"),
                "unhealthy_deployments": deployments.get("unhealthy_deployments", []),
            },
        ),
        _section(
            "Networking Findings",
            {
                "healthy": network.get("healthy"),
                "problematic_services": network.get("problematic_services", []),
            },
        ),
    ]
    return "\n\n".join(sections)


def build_messages(investigation: dict[str, Any]) -> list[dict[str, str]]:
    """Build the chat messages (system + user) for the LLM."""
    user_prompt = (
        "Diagnose the following Kubernetes incident based strictly on this evidence.\n\n"
        + summarize_evidence(investigation)
        + "\n\nReturn only the JSON object described in the system instructions."
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
