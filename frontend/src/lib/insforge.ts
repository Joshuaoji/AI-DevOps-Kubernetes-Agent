import { createClient, type InsForgeClient } from "@insforge/sdk";

/**
 * Lazily-created singleton InsForge browser client (SPA style). Created only in
 * the browser so it never runs during server rendering. Uses the public anon
 * key + project URL from NEXT_PUBLIC env vars.
 */
let client: InsForgeClient | null = null;

export function getInsforge(): InsForgeClient {
  if (!client) {
    client = createClient({
      baseUrl: process.env.NEXT_PUBLIC_INSFORGE_URL as string,
      anonKey: process.env.NEXT_PUBLIC_INSFORGE_ANON_KEY as string,
    });
  }
  return client;
}
