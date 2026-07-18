"use client";

import { useCallback, useRef, useState } from "react";

import { getInsforge } from "@/lib/insforge";
import { runInvestigation, InvestigateError } from "@/services/api";
import type { Diagnosis, ProgressStep, StepStatus } from "@/types";

const STEP_DEFS: Array<{ key: string; label: string }> = [
  { key: "pods", label: "Checking Pods" },
  { key: "logs", label: "Reading Logs" },
  { key: "events", label: "Analyzing Events" },
  { key: "deployments", label: "Inspecting Deployments" },
  { key: "network", label: "Checking Networking" },
  { key: "reasoning", label: "AI Reasoning" },
  { key: "root_cause", label: "Root Cause Found" },
];

const initialSteps = (): ProgressStep[] =>
  STEP_DEFS.map((s) => ({ ...s, status: "pending" as StepStatus }));

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

type Status = "idle" | "running" | "done" | "error";

export function useInvestigation(onComplete?: () => void) {
  const [status, setStatus] = useState<Status>("idle");
  const [steps, setSteps] = useState<ProgressStep[]>(initialSteps);
  const [diagnosis, setDiagnosis] = useState<Diagnosis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const channelRef = useRef<string | null>(null);

  const applyStep = useCallback((key: string, stepStatus: StepStatus) => {
    setSteps((prev) =>
      prev.map((s) => (s.key === key ? { ...s, status: stepStatus } : s)),
    );
  }, []);

  const investigate = useCallback(async () => {
    setStatus("running");
    setError(null);
    setDiagnosis(null);
    setSteps(initialSteps());

    const insforge = getInsforge();
    const runId =
      typeof crypto !== "undefined" && "randomUUID" in crypto
        ? crypto.randomUUID()
        : String(Date.now());
    const channel = `investigation:${runId}`;
    channelRef.current = channel;

    // Best-effort realtime: publish progress so it broadcasts (and syncs to any
    // other subscribed tab/device). The local UI also updates directly so a
    // realtime hiccup never blocks the core UX.
    let realtimeReady = false;
    try {
      await insforge.realtime.connect();
      const sub = await insforge.realtime.subscribe(channel);
      realtimeReady = Boolean(sub?.ok);
      insforge.realtime.on("step", (payload: { key: string; status: StepStatus }) => {
        applyStep(payload.key, payload.status);
      });
    } catch {
      realtimeReady = false;
    }

    const publishStep = async (key: string, stepStatus: StepStatus) => {
      applyStep(key, stepStatus);
      if (realtimeReady) {
        try {
          await insforge.realtime.publish(channel, "step", { key, status: stepStatus });
        } catch {
          /* broadcasting is best-effort */
        }
      }
    };

    // Kick off the real backend call immediately.
    const apiPromise = runInvestigation();

    // Tick through the evidence-gathering stages while the request runs.
    const pipeline = ["pods", "logs", "events", "deployments", "network"];
    for (const key of pipeline) {
      await publishStep(key, "active");
      await delay(550);
      await publishStep(key, "done");
    }
    await publishStep("reasoning", "active");

    try {
      const response = await apiPromise;
      await publishStep("reasoning", "done");
      await publishStep("root_cause", "done");
      setDiagnosis(response.diagnosis);
      setStatus("done");
      await saveHistory(response);
      onComplete?.();
    } catch (err) {
      const message =
        err instanceof InvestigateError ? err.message : "Investigation failed.";
      setError(message);
      setStatus("error");
      setSteps((prev) =>
        prev.map((s) => (s.status === "active" ? { ...s, status: "error" } : s)),
      );
    } finally {
      if (realtimeReady && channelRef.current) {
        try {
          insforge.realtime.unsubscribe(channelRef.current);
        } catch {
          /* ignore */
        }
      }
    }
  }, [applyStep, onComplete]);

  return { status, steps, diagnosis, error, investigate };
}

/** Persist a lightweight summary of the investigation to InsForge history. */
async function saveHistory(response: {
  investigation: {
    meta?: { cluster_reachable?: boolean; overall_healthy?: boolean | null };
    pods?: { problematic_pods?: Array<{ namespace: string }> };
  };
  diagnosis: Diagnosis;
}) {
  const meta = response.investigation.meta ?? {};
  const namespace =
    response.investigation.pods?.problematic_pods?.[0]?.namespace ?? "default";
  const status =
    meta.cluster_reachable === false
      ? "cluster_unreachable"
      : meta.overall_healthy
        ? "healthy"
        : "issues_found";

  try {
    await getInsforge()
      .database.from("investigations")
      .insert([
        {
          root_cause: response.diagnosis.root_cause ?? "N/A",
          namespace,
          confidence: response.diagnosis.confidence ?? null,
          status,
        },
      ]);
  } catch {
    /* history is non-critical; never block the UX on a save failure */
  }
}
