# Documentation

Project documentation for the **AI Kubernetes Agent**.

## Architecture

```text
Frontend (Next.js)
    ↓
FastAPI Backend (Orchestrator)
    ↓
Kubernetes Investigation Layer   (placeholder)
    ↓
AI Kubernetes Agent              (placeholder)
    ↓
LLM Reasoning (OpenRouter via InsForge)   (later iteration)
    ↓
Root Cause + Suggested Fix
    ↓
Frontend Diagnosis
```

This is an **on-demand troubleshooting system**, not a Kubernetes controller/operator.

## Status

Foundation only. Kubernetes inspection, AI reasoning, OpenRouter, InsForge,
auth, and realtime are intentionally **not** implemented yet.
