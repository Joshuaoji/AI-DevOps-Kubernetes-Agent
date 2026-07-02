"use client";

/**
 * Placeholder action button. The real investigation flow (API call -> AI
 * diagnosis) is wired up in a later iteration; for now this is UI only.
 */
export function InvestigateButton() {
  return (
    <button
      type="button"
      className="rounded-lg bg-blue-600 px-6 py-3 text-base font-semibold text-white shadow-sm transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
    >
      Investigate Cluster
    </button>
  );
}
