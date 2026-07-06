"""AI Kubernetes agent.

Consumes the investigation evidence, asks the LLM (via OpenRouter) to reason like
a Senior SRE, and returns a structured :class:`Diagnosis` (root cause, fix,
kubectl commands, prevention, confidence). No secrets are logged or returned.
"""

from __future__ import annotations

import json
import re
from typing import Any

# Reasoning models sometimes wrap their chain-of-thought in <think>...</think>.
_THINK_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)

from app.ai.llm_client import OpenRouterClient
from app.ai.prompt_builder import build_messages
from app.core.logging import logger
from app.models.diagnosis import Diagnosis


def _strip_code_fences(text: str) -> str:
    """Remove ```json ... ``` fences some models wrap JSON in."""
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("\n", 1)[-1] if "\n" in stripped else stripped
        if stripped.endswith("```"):
            stripped = stripped[: -3]
        # drop a leading language tag left on the first line
        if stripped.lower().startswith("json"):
            stripped = stripped[4:]
    return stripped.strip()


def _extract_json(text: str) -> dict[str, Any] | None:
    """Best-effort parse of a JSON object from the model output.

    Tolerates code fences and reasoning-model preambles (``<think>`` blocks or
    prose before the JSON) by falling back to the last complete ``{...}`` block.
    """
    candidate = _strip_code_fences(_THINK_BLOCK.sub("", text))
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass
    # Fallback: grab the outermost {...} block (handles prepended reasoning).
    start, end = candidate.find("{"), candidate.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(candidate[start : end + 1])
        except json.JSONDecodeError:
            return None
    return None


def _clamp_confidence(value: Any) -> int | None:
    """Coerce the model's confidence into an integer 0-100."""
    try:
        number = int(round(float(value)))
    except (TypeError, ValueError):
        return None
    return max(0, min(100, number))


class AIKubernetesAgent:
    """Turns investigation evidence into an SRE-style diagnosis."""

    def __init__(self, client: OpenRouterClient | None = None) -> None:
        self.client = client or OpenRouterClient()

    def diagnose(self, investigation: dict[str, Any]) -> Diagnosis:
        """Produce a diagnosis from the investigation payload."""
        meta = investigation.get("meta", {}) or {}

        # Nothing to reason about if we could not reach the cluster.
        if meta.get("cluster_reachable") is False:
            return Diagnosis.unavailable(
                "Skipped AI reasoning: cluster is not reachable, so there is no evidence to analyze."
            )

        # If everything is healthy, there is no incident to diagnose.
        if meta.get("overall_healthy") is True:
            return Diagnosis(
                available=True,
                root_cause="No problems detected",
                explanation="Pods, deployments, and networking all look healthy in the collected evidence.",
                confidence=100,
                confidence_reasoning="All inspectors reported healthy state with no problematic resources.",
                model=self.client.settings.resolved_model,
            )

        messages = build_messages(investigation)
        result = self.client.chat(messages)

        if not result.success:
            logger.warning("AI diagnosis unavailable: {err}", err=result.error)
            return Diagnosis.unavailable(f"LLM call failed: {result.error}")

        parsed = _extract_json(result.content)
        if parsed is None:
            logger.warning("Could not parse LLM output as JSON")
            return Diagnosis(
                available=False,
                error="Could not parse the model response as JSON.",
                explanation=result.content[:500] or None,
                model=result.model,
            )

        commands = parsed.get("kubectl_commands") or []
        if isinstance(commands, str):
            commands = [commands]
        commands = [str(c).strip() for c in commands if str(c).strip()]

        logger.info("AI diagnosis produced (model={model})", model=result.model)
        return Diagnosis(
            available=True,
            root_cause=parsed.get("root_cause"),
            explanation=parsed.get("explanation"),
            fix=parsed.get("suggested_fix") or parsed.get("fix"),
            kubectl_command=commands[0] if commands else None,
            kubectl_commands=commands,
            prevention=parsed.get("prevention"),
            confidence=_clamp_confidence(parsed.get("confidence")),
            confidence_reasoning=parsed.get("confidence_reasoning"),
            model=result.model,
        )
