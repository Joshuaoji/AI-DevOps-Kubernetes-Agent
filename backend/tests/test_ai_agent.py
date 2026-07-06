"""Unit tests for the AI Kubernetes agent (uses a fake LLM client)."""

from types import SimpleNamespace

from app.ai.agent import AIKubernetesAgent
from app.ai.llm_client import LLMResult

VALID_JSON = """{
  "root_cause": "DATABASE_URL environment variable is missing",
  "explanation": "The payment pod crashes on startup because it cannot read DATABASE_URL.",
  "suggested_fix": "Add the DATABASE_URL env var to the deployment.",
  "kubectl_commands": ["kubectl edit deployment payment-service -n shop", "kubectl rollout restart deployment payment-service -n shop"],
  "prevention": "Validate required env vars in CI and use a ConfigMap/Secret.",
  "confidence": 92,
  "confidence_reasoning": "CrashLoopBackOff plus a clear missing-env log line."
}"""

BROKEN_META = {"meta": {"cluster_reachable": True, "overall_healthy": False},
               "pods": {"problematic_pods": [{"name": "payment-1", "status": "CrashLoopBackOff"}]}}


class FakeClient:
    def __init__(self, result: LLMResult):
        self._result = result
        self.settings = SimpleNamespace(resolved_model="fake/model")

    def chat(self, messages, *, temperature: float = 0.0) -> LLMResult:
        return self._result


def test_parses_valid_diagnosis():
    agent = AIKubernetesAgent(client=FakeClient(LLMResult(True, content=VALID_JSON, model="fake/model")))
    diag = agent.diagnose(BROKEN_META)

    assert diag.available is True
    assert "DATABASE_URL" in diag.root_cause
    assert diag.fix.startswith("Add the DATABASE_URL")
    assert diag.kubectl_command == "kubectl edit deployment payment-service -n shop"
    assert len(diag.kubectl_commands) == 2
    assert diag.confidence == 92


def test_parses_json_wrapped_in_code_fence():
    fenced = f"```json\n{VALID_JSON}\n```"
    agent = AIKubernetesAgent(client=FakeClient(LLMResult(True, content=fenced, model="fake/model")))
    diag = agent.diagnose(BROKEN_META)
    assert diag.available is True
    assert diag.confidence == 92


def test_confidence_is_clamped():
    content = VALID_JSON.replace("92", "150")
    agent = AIKubernetesAgent(client=FakeClient(LLMResult(True, content=content, model="fake/model")))
    diag = agent.diagnose(BROKEN_META)
    assert diag.confidence == 100


def test_llm_failure_is_graceful():
    agent = AIKubernetesAgent(client=FakeClient(LLMResult(False, error="HTTP 429")))
    diag = agent.diagnose(BROKEN_META)
    assert diag.available is False
    assert "429" in diag.error


def test_unparseable_output_is_graceful():
    agent = AIKubernetesAgent(client=FakeClient(LLMResult(True, content="not json at all", model="fake/model")))
    diag = agent.diagnose(BROKEN_META)
    assert diag.available is False
    assert "parse" in diag.error.lower()


def test_skips_when_cluster_unreachable():
    agent = AIKubernetesAgent(client=FakeClient(LLMResult(True, content=VALID_JSON)))
    diag = agent.diagnose({"meta": {"cluster_reachable": False}})
    assert diag.available is False
    assert "not reachable" in diag.error


def test_healthy_cluster_needs_no_llm():
    agent = AIKubernetesAgent(client=FakeClient(LLMResult(False, error="should not be called")))
    diag = agent.diagnose({"meta": {"cluster_reachable": True, "overall_healthy": True}})
    assert diag.available is True
    assert diag.root_cause == "No problems detected"
    assert diag.confidence == 100
