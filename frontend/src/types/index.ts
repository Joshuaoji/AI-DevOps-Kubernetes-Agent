/** Shared frontend types for the AI Kubernetes Agent dashboard. */

export interface Diagnosis {
  available: boolean;
  root_cause: string | null;
  explanation: string | null;
  fix: string | null;
  kubectl_command: string | null;
  kubectl_commands: string[];
  prevention: string | null;
  confidence: number | null;
  confidence_reasoning: string | null;
  model: string | null;
  error: string | null;
}

export interface InvestigateResponse {
  status: string;
  investigation: {
    meta?: { cluster_reachable?: boolean; overall_healthy?: boolean | null };
    pods?: {
      problematic_pods?: Array<{ name: string; namespace: string; status: string }>;
    };
  };
  diagnosis: Diagnosis;
}

/** A row in the InsForge `investigations` history table. */
export interface InvestigationRecord {
  id: string;
  root_cause: string | null;
  namespace: string | null;
  confidence: number | null;
  status: string;
  created_at: string;
}

export type StepStatus = "pending" | "active" | "done" | "error";

export interface ProgressStep {
  key: string;
  label: string;
  status: StepStatus;
}
