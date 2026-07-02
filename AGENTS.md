# AGENTS.md

<!-- INSFORGE:START -->
## InsForge backend

This project uses [InsForge](https://insforge.dev): an all-in-one, open-source Postgres-based backend (BaaS) that gives this app a database, authentication, file storage, edge functions, realtime, an AI model gateway, and payments through one platform.

- **Project:** **AI-DevOps-Kubernetes-Agent** (API base `https://4y9trv6y.us-east.insforge.app`)
- **Skills:** these InsForge skills are installed for supported coding agents. Reach for them before implementing any InsForge feature instead of guessing the API:
  - `insforge`: app code with the `@insforge/sdk` client (database CRUD, auth, storage, edge functions, realtime, AI, email, and Stripe payments).
  - `insforge-cli`: backend and infrastructure via the `insforge` CLI (projects, SQL, migrations, RLS policies, storage buckets, functions, secrets, payment setup, schedules, deploys).
  - `insforge-debug`: diagnosing failures (SDK/HTTP errors, RLS denials, auth and OAuth issues) and running security or performance audits.
  - `insforge-integrations`: wiring external auth providers (Clerk, Auth0, WorkOS, Better Auth, etc.) for JWT-based RLS, or the OKX x402 payment facilitator.
  - `find-skills`: discovering additional skills on demand.
- **Credentials:** app code reads keys from `.env.local`; the CLI reads `.insforge/project.json`. Never hardcode or commit keys.

Key patterns:

- Database inserts take an array: `insert([{ ... }])`.
- Reference users with `auth.users(id)`; use `auth.uid()` in RLS policies.
- For storage uploads, persist both the returned `url` and `key`.
<!-- INSFORGE:END -->

## Cursor Cloud specific instructions

This repo uses **InsForge** as its backend. The CLI auth (`~/.insforge/credentials.json`) and the project link (`.insforge/project.json`) are already established and persist in the VM snapshot, so you normally do NOT need to re-run `login`/`link`.

- Run the CLI via `npx @insforge/cli <command>` (there is no global `insforge` binary). Verify connection with `npx @insforge/cli current`; health with `npx @insforge/cli diagnose`; backend inventory with `npx @insforge/cli metadata`.
- Linked project: **AI-DevOps-Kubernetes-Agent**, API base `https://4y9trv6y.us-east.insforge.app`. Backend is Postgres 15 and currently has no tables/buckets/functions.
- If auth ever expires, re-link with `npx @insforge/cli link --project-id c511090c-43a4-41a3-942b-2aa00ada7344` (re-login first if needed). `.insforge/` and the agent-skill dirs are git-ignored — never commit them.
- Gotcha: `npx @insforge/cli db query "<sql>"` with multiple statements returns only an empty `rows` array for the batch; run a standalone `SELECT` afterward to see results.
- App code (once added) reads InsForge keys from `.env.local`; never hardcode or commit keys. Prefer migrations (`db migrations`) over ad-hoc `db query` for schema changes.
