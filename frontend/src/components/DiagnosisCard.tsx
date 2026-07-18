"use client";

import type { Diagnosis } from "@/types";

function Field({ label, value }: { label: string; value: string | null }) {
  if (!value) return null;
  return (
    <div>
      <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
        {label}
      </div>
      <div className="mt-1 text-sm text-slate-800">{value}</div>
    </div>
  );
}

export function DiagnosisCard({ diagnosis }: { diagnosis: Diagnosis }) {
  if (!diagnosis.available) {
    return (
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-6 shadow-sm">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-amber-700">
          Diagnosis
        </h2>
        <p className="mt-2 text-sm text-amber-800">
          {diagnosis.error ?? "AI reasoning is unavailable."}
        </p>
      </div>
    );
  }

  const commands =
    diagnosis.kubectl_commands.length > 0
      ? diagnosis.kubectl_commands
      : diagnosis.kubectl_command
        ? [diagnosis.kubectl_command]
        : [];

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
          Diagnosis
        </h2>
        {typeof diagnosis.confidence === "number" && (
          <span className="rounded-full bg-blue-50 px-3 py-1 text-sm font-semibold text-blue-700">
            Confidence: {diagnosis.confidence}%
          </span>
        )}
      </div>

      <div className="mt-4 space-y-4">
        <Field label="Root Cause" value={diagnosis.root_cause} />
        <Field label="Explanation" value={diagnosis.explanation} />
        <Field label="Suggested Fix" value={diagnosis.fix} />

        {commands.length > 0 && (
          <div>
            <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              kubectl Command{commands.length > 1 ? "s" : ""}
            </div>
            <div className="mt-1 space-y-1">
              {commands.map((cmd) => (
                <pre
                  key={cmd}
                  className="overflow-x-auto rounded-md bg-slate-900 px-3 py-2 text-xs text-slate-100"
                >
                  {cmd}
                </pre>
              ))}
            </div>
          </div>
        )}

        <Field label="Prevention" value={diagnosis.prevention} />
      </div>
    </div>
  );
}
