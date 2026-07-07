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

### Communication preference

- When responding in chat, surface your reasoning/thought process — the plan, trade-offs, why you chose an approach, and how you interpret test results — not just the final solution. Keep it skimmable: expand for non-obvious decisions (architecture, debugging, testing strategy) and stay brief for trivial steps.

This repo uses **InsForge** as its backend. The CLI auth (`~/.insforge/credentials.json`) and the project link (`.insforge/project.json`) are already established and persist in the VM snapshot, so you normally do NOT need to re-run `login`/`link`.

- Run the CLI via `npx @insforge/cli <command>` (there is no global `insforge` binary). Verify connection with `npx @insforge/cli current`; health with `npx @insforge/cli diagnose`; backend inventory with `npx @insforge/cli metadata`.
- Linked project: **AI-DevOps-Kubernetes-Agent**, API base `https://4y9trv6y.us-east.insforge.app`. Backend is Postgres 15 and currently has no tables/buckets/functions.
- If auth ever expires, re-link with `npx @insforge/cli link --project-id c511090c-43a4-41a3-942b-2aa00ada7344` (re-login first if needed). `.insforge/` and the agent-skill dirs are git-ignored — never commit them.
- Gotcha: `npx @insforge/cli db query "<sql>"` with multiple statements returns only an empty `rows` array for the batch; run a standalone `SELECT` afterward to see results.
- App code (once added) reads InsForge keys from `.env.local`; never hardcode or commit keys. Prefer migrations (`db migrations`) over ad-hoc `db query` for schema changes.

### Project layout & running services

Monorepo: `backend/` (FastAPI) and `frontend/` (Next.js 14 App Router). See `README.md` for the standard run commands; notes below are the non-obvious bits.

- **Backend** lives under `backend/app` (`api`, `core`, `kubernetes`, `ai`, `services`, `models`). Uses a Python venv at `backend/.venv`. Run dev: `cd backend && . .venv/bin/activate && uvicorn app.main:app --reload --port 8000`. Settings load from `backend/.env` via `pydantic-settings`; copy `backend/.env.example` to `backend/.env`. Health: `GET /health`.
- **Frontend** dev: `cd frontend && npm run dev` (port 3000). Env from `frontend/.env.local` (copy from `.env.example`); `NEXT_PUBLIC_API_BASE_URL` points at the backend.
- **Gotcha (important):** never run `npm run build` in `frontend/` while `next dev` is running — both use the same `.next/` directory, and the build clobbers it, leaving the dev server serving broken/unstyled assets (Tailwind CSS silently disappears). If styles vanish, stop dev, `rm -rf frontend/.next`, and restart `npm run dev`.
- `kubernetes/`, `services/investigation.py`, and `ai/` are all implemented now. Do not break the health endpoint or the run/build flow when extending them.
- Docker: `docker compose up --build` runs backend (8000) + frontend (3000). Docker is NOT preinstalled on the VM; prefer the dev servers above for local iteration.

### Kubernetes investigation layer

- `POST /investigate` shells out to `kubectl` (subprocess, not the Python SDK) via `app/kubernetes/executor.py` and returns structured evidence. It **degrades gracefully**: with no reachable cluster it still returns `200` with `meta.cluster_reachable=false` and per-section errors.
- Backend tests: `cd backend && . .venv/bin/activate && python -m pytest` (parsers + orchestration; `requirements-dev.txt` adds pytest). Parser logic is split from subprocess calls so it is unit-testable without a cluster.
- **Cluster gotcha:** a real in-VM Kubernetes cluster (kind / k3d / k3s) does NOT come up in the Cloud VM — kubelet/k3s hit cgroup v2 "domain controllers invalid state" and nested overlay limits. Don't burn time trying to boot one. To exercise the full pipeline against realistic data, set `KUBECTL_BINARY` to a stub script that prints canned `kubectl ... -o json` output (see the `FakeExecutor` in `backend/tests/test_investigation_service.py` for the shape), or rely on the pytest suite.

### AI reasoning layer

- `POST /investigate` now also returns a `diagnosis` (Senior-SRE root cause, fix, kubectl commands, prevention, confidence) produced by `app/ai/` from the evidence. The `investigation` evidence is still returned alongside it (backward compatible).
- The OpenRouter key is provisioned by InsForge, not hardcoded: `npx @insforge/cli ai setup --env-file backend/.env` writes `OPENROUTER_API_KEY`. Also set `OPENROUTER_MODEL`. `backend/.env` is git-ignored — never commit the key.
- Degrades gracefully: with no key, an unreachable cluster, a healthy cluster, or an LLM/parse failure, `/investigate` still returns `200` with `diagnosis.available=false` (and a reason) or a "no problems detected" diagnosis.
- **Free-model gotcha:** the InsForge org has $0 credits, so only OpenRouter `:free` models work, and they are rate-limited/intermittent (HTTP 429 or long stalls). Prefer an *instruct* model (e.g. `nvidia/nemotron-nano-12b-v2-vl:free`) over a reasoning model — reasoning models spend the token budget "thinking" and get truncated before emitting JSON. If a call fails, just retry; the client already retries transient 429/5xx.

### Frontend dashboard + InsForge (auth / realtime / history)

- The frontend (`frontend/src/`) is a client-side SPA dashboard using `@insforge/sdk` for **auth**, **realtime progress**, and **investigation history**; FastAPI stays the orchestrator (`POST /investigate`).
- Frontend env (`frontend/.env.local`, git-ignored): `NEXT_PUBLIC_INSFORGE_URL` (= `oss_host`), `NEXT_PUBLIC_INSFORGE_ANON_KEY` (get via `npx @insforge/cli secrets get ANON_KEY`), `NEXT_PUBLIC_API_BASE_URL`. **Restart `next dev` after changing env** — `NEXT_PUBLIC_*` is inlined at startup.
- Backend state used by this feature (already applied to the InsForge project, persists): email verification disabled (`insforge.toml` → `config apply`), `public.investigations` table (user-scoped RLS) and realtime channel pattern `investigation:%` (both from `migrations/`). Re-apply with `db migrations up --all` / `config apply` if pointing at a fresh backend/branch.
- **Auth reload gotcha:** the SPA root client keeps the access token in memory and refreshes via an httpOnly cookie on the InsForge domain. From `localhost:3000` that cookie is cross-origin and not sent, so you'll see harmless `401 /api/auth/refresh` logs and the session does NOT survive a full page reload (it works fine within a session). For persistent sessions use the `@insforge/sdk/ssr` helpers.
- To see a populated diagnosis in the dashboard, run the backend against the broken-cluster stub (`KUBECTL_BINARY=/tmp/fake-bin/kubectl`) since a real cluster can't run in the VM (see cluster gotcha above).
