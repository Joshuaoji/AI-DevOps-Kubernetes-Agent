# AI-DevOps-Kubernetes-Agent

An **AI Kubernetes Troubleshooting Agent** — an on-demand system that
investigates a Kubernetes cluster and uses AI reasoning to surface a root cause
and suggested fix.

> This repository currently contains the **project foundation only**.
> Kubernetes inspection, AI reasoning, OpenRouter, and InsForge integration are
> added in later iterations.

## Architecture

```text
Frontend  ->  FastAPI Backend (Orchestrator)  ->  Kubernetes Investigation
          ->  AI Kubernetes Agent  ->  LLM Reasoning (OpenRouter via InsForge)
          ->  Root Cause + Suggested Fix  ->  Frontend Diagnosis
```

This is an on-demand troubleshooting system, **not** a Kubernetes
controller/operator.

## Project structure

```text
.
├── backend/      # FastAPI backend (api, core, kubernetes, ai, services, models)
├── frontend/     # Next.js + TypeScript + Tailwind frontend
├── docs/         # Project documentation
├── prompts/      # Iterative build prompts
├── docker-compose.yml
└── README.md
```

## Tech stack

- **Backend:** FastAPI, Python 3.12+, Uvicorn, Pydantic, Loguru, HTTPX
- **Frontend:** Next.js, TypeScript, Tailwind CSS, Axios, React Query
- **Infrastructure:** Docker, Docker Compose

## Quick start (Docker)

```bash
docker compose up --build
```

Then open:

- Frontend: <http://localhost:3000>
- Backend health: <http://localhost:8000/health>

## Local development (without Docker)

Backend:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

## Environment variables

Backend (`backend/.env`):

```env
OPENROUTER_API_KEY=
OPENROUTER_MODEL=
KUBECONFIG_PATH=
CORS_ORIGINS=http://localhost:3000
```

Frontend (`frontend/.env.local`):

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```
