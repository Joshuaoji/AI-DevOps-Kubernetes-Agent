"use client";

import { useState } from "react";

import { DiagnosisCard } from "@/components/DiagnosisCard";
import { HistoryList } from "@/components/HistoryList";
import { InvestigationProgress } from "@/components/InvestigationProgress";
import { useAuth } from "@/context/AuthContext";
import { useInvestigation } from "@/hooks/useInvestigation";

export function Dashboard() {
  const { user, signOut } = useAuth();
  const [reloadSignal, setReloadSignal] = useState(0);
  const { status, steps, diagnosis, error, investigate } = useInvestigation(() =>
    setReloadSignal((n) => n + 1),
  );

  const running = status === "running";

  return (
    <main className="mx-auto min-h-screen max-w-2xl px-6 py-10">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">AI Kubernetes Agent</h1>
        <div className="flex items-center gap-3 text-sm text-slate-500">
          <span className="hidden sm:inline">{user?.email}</span>
          <button
            type="button"
            onClick={() => void signOut()}
            className="rounded-md border border-slate-300 px-3 py-1 text-slate-700 transition-colors hover:bg-slate-100"
          >
            Sign out
          </button>
        </div>
      </header>

      <p className="mt-2 text-slate-500">Troubleshoot Kubernetes with AI</p>

      <div className="mt-6">
        <button
          type="button"
          onClick={() => void investigate()}
          disabled={running}
          className="rounded-lg bg-blue-600 px-6 py-3 text-base font-semibold text-white shadow-sm transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {running ? "Investigating…" : "Investigate Cluster"}
        </button>
      </div>

      {error && (
        <p className="mt-6 rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </p>
      )}

      <div className="mt-8 space-y-6">
        {status !== "idle" && <InvestigationProgress steps={steps} />}
        {diagnosis && <DiagnosisCard diagnosis={diagnosis} />}
        <HistoryList reloadSignal={reloadSignal} />
      </div>
    </main>
  );
}
