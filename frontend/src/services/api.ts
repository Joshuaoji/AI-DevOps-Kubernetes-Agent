import axios from "axios";

import type { InvestigateResponse } from "@/types";

/**
 * Shared Axios instance pointed at the FastAPI backend (the orchestrator).
 */
export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
});

/** Human-readable error for the UI. */
export class InvestigateError extends Error {}

/**
 * Call the backend to run an investigation. Handles timeouts and surfaces a
 * clean error message for the UI (loading/empty/failure states live in the UI).
 */
export async function runInvestigation(): Promise<InvestigateResponse> {
  try {
    const { data } = await apiClient.post<InvestigateResponse>(
      "/investigate",
      {},
      { timeout: 120_000 },
    );
    if (!data || !data.diagnosis) {
      throw new InvestigateError("The backend returned an empty response.");
    }
    return data;
  } catch (err) {
    if (axios.isAxiosError(err)) {
      if (err.code === "ECONNABORTED") {
        throw new InvestigateError("The investigation timed out. Please try again.");
      }
      if (err.response) {
        throw new InvestigateError(
          `Backend error (${err.response.status}). Please try again.`,
        );
      }
      throw new InvestigateError(
        "Could not reach the backend. Is it running on port 8000?",
      );
    }
    throw err instanceof InvestigateError
      ? err
      : new InvestigateError("Unexpected error running the investigation.");
  }
}
