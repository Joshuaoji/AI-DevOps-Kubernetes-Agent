# 01-prompt-project-setup.md

This directory stores the build prompts used to iteratively develop the
AI Kubernetes Agent.

The first prompt established the project foundation:

- FastAPI backend with a `GET /health` endpoint, CORS, logging (Loguru), and
  environment loading.
- Next.js (TypeScript) frontend with Tailwind CSS, Axios, and React Query, plus
  a minimal homepage.
- Docker + Docker Compose setup (backend on port 8000, frontend on port 3000).
- Monorepo folder structure with placeholders for the Kubernetes and AI layers.

No Kubernetes logic, AI reasoning, OpenRouter, InsForge, auth, or realtime was
implemented in this step.
