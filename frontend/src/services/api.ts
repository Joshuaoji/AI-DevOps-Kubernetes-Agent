import axios from "axios";

/**
 * Shared Axios instance pointed at the FastAPI backend. Feature-specific
 * service functions are added in later iterations.
 */
export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
  headers: {
    "Content-Type": "application/json",
  },
});
