# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Def-Space Multi-Agent Intelligence Dashboard — a BSERC college project (4-person team).
FastAPI backend (one agent per folder under `backend/app/agents/`) + React/Vite frontend.
Full architecture diagram, setup steps, and API key behavior are documented in README.md —
read that first; don't duplicate it here.

## Running locally

- Backend: `cd backend && .\venv\Scripts\python.exe -m uvicorn app.main:app --reload`
  (requires the existing Python 3.12 venv — see below). Docs at `/docs`.
- Frontend: `cd frontend && npm run dev`
- Frontend lint: `npm run lint` (this project uses **oxlint**, not ESLint)
- **No automated test suite exists yet** (no pytest, no vitest/jest anywhere in the repo).
  Verify backend changes via `http://127.0.0.1:8000/docs`; verify frontend changes in the
  running browser session.

## Non-negotiables

- **Never mock or fake data.** Every key-gated agent (News, RAG, Vision's Gemini
  description, Translation, Report's LLM prose) must return `status: "not_configured"`
  when its API key is absent — never fabricate a response. This is a hard project
  requirement, not a style preference.
- **GIS must not invent map pins.** Free-tier news APIs don't return per-article
  coordinates — only plot real, derivable geometry (e.g. AOI center).

## Python version

Must use **Python 3.12**, not 3.13/3.14 — `chromadb`'s native dependency
(`chroma-hnswlib`) has no prebuilt Windows wheel for newer versions and would need a full
C++ build toolchain to compile from source. The existing `backend/venv` is already built
against 3.12.10 — don't recreate it against a different interpreter.

## Shared contract

`backend/app/models/schemas.py` (Pydantic) and `frontend/src/api/types.ts` (TypeScript)
must be kept in sync **by hand** — there is no codegen between them. Changing one without
updating the other will silently desync frontend and backend.

## Adding a new agent

Follow the existing pattern: one folder under `backend/app/agents/<name>/` with
`service.py` (logic) + `routes.py` (FastAPI router), registered in `backend/app/main.py`.
Update `schemas.py` and hand-mirror the change in `types.ts`.

## Git

Local repo, intended remote: `github.com/rgarg-lab`. Commit directly to main — no
branch/PR convention in place.
