"use client";

import type { ProgressStep } from "@/types";

const ICON: Record<ProgressStep["status"], string> = {
  pending: "○",
  active: "◍",
  done: "✓",
  error: "✕",
};

const COLOR: Record<ProgressStep["status"], string> = {
  pending: "text-slate-400",
  active: "text-blue-600 animate-pulse",
  done: "text-green-600",
  error: "text-red-600",
};

export function InvestigationProgress({ steps }: { steps: ProgressStep[] }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
        Investigation Status
      </h2>
      <ul className="mt-4 space-y-2">
        {steps.map((step) => (
          <li key={step.key} className="flex items-center gap-3 text-sm">
            <span className={`w-4 text-center font-bold ${COLOR[step.status]}`}>
              {ICON[step.status]}
            </span>
            <span
              className={
                step.status === "pending" ? "text-slate-400" : "text-slate-800"
              }
            >
              {step.label}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
