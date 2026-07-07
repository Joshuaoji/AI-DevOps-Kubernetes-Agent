"use client";

import { useEffect, useState } from "react";

import { getInsforge } from "@/lib/insforge";
import type { InvestigationRecord } from "@/types";

const STATUS_STYLES: Record<string, string> = {
  issues_found: "bg-red-50 text-red-700",
  healthy: "bg-green-50 text-green-700",
  cluster_unreachable: "bg-slate-100 text-slate-600",
};

export function HistoryList({ reloadSignal }: { reloadSignal: number }) {
  const [records, setRecords] = useState<InvestigationRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      const { data } = await getInsforge()
        .database.from("investigations")
        .select("id, root_cause, namespace, confidence, status, created_at")
        .order("created_at", { ascending: false })
        .limit(10);
      if (!cancelled) {
        setRecords((data as InvestigationRecord[]) ?? []);
        setLoading(false);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [reloadSignal]);

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
        Recent Investigations
      </h2>

      {loading ? (
        <p className="mt-4 text-sm text-slate-400">Loading…</p>
      ) : records.length === 0 ? (
        <p className="mt-4 text-sm text-slate-400">No investigations yet.</p>
      ) : (
        <ul className="mt-4 divide-y divide-slate-100">
          {records.map((rec) => (
            <li key={rec.id} className="flex items-center justify-between gap-3 py-3">
              <div className="min-w-0">
                <div className="truncate text-sm font-medium text-slate-800">
                  {rec.root_cause ?? "N/A"}
                </div>
                <div className="text-xs text-slate-400">
                  {rec.namespace ?? "default"} ·{" "}
                  {new Date(rec.created_at).toLocaleString()}
                </div>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                {typeof rec.confidence === "number" && (
                  <span className="text-xs font-medium text-slate-500">
                    {rec.confidence}%
                  </span>
                )}
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                    STATUS_STYLES[rec.status] ?? "bg-slate-100 text-slate-600"
                  }`}
                >
                  {rec.status.replace(/_/g, " ")}
                </span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
