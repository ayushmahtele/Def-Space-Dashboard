# Session Handoff — 2026-08-01

Status snapshot for resuming work on the 4 features in `docs/BUILD_SPEC.md`. All four
are implemented and wired end-to-end; the main gap is **visual verification in an actual
browser never happened** (Chrome extension wasn't connected this session) — do that
first before considering this done.

## What's done

1. **Intro sequence** — `frontend/src/components/intro/`. Particle-assembly "BSERC"
   text wordmark (loading screen) → welcome screen (Option A copy) → dashboard. Wired
   in `frontend/src/main.tsx` ahead of `<App />`.
2. **Guided tutorial** — `frontend/src/components/tutorial/`. Original 3D probe-bot
   mascot (primitive Three.js geometry). Steps: Map → Watchlist → SITREP feed →
   Go/No-Go result. Skippable, replays every visit (no localStorage gate, per your
   choice). Anchors via `data-tutorial="..."` attributes added to `App.tsx`.
3. **Predict agent (go/no-go model)** — `backend/app/agents/predict/`. RandomForest +
   SHAP, trained on **469 real rows** combining SpaceX's own published launch-weather-go
   probability (Launch Library 2 API) with real historical weather at each pad
   (Open-Meteo). Full provenance in `backend/data/launch_weather/PROVENANCE.md`. Wired
   into the orchestrator (`backend/app/orchestrator/intent.py` + `run.py` — triggers on
   launch-related keywords), the Report agent's claims/severity
   (`backend/app/agents/report/claims.py`, `severity.py`), and the UI
   (`frontend/src/components/predict/PredictPanel.tsx`).
4. **3D workflow visualization** — `frontend/src/components/workflow/`. Standalone
   "Workflow" tab (toggle added to `Header.tsx`). **Updated 2026-08-01 (later in the
   session):** replaced the original from-scratch Three.js/`@react-three/fiber` scene
   with the third-party Orchestration UI Kit supplied at `docs/orchestration_ui_kit/`
   (CSS `perspective`/`transform` 3D, not WebGL) — ported to TypeScript at
   `frontend/src/vendor/orchestration-kit/OrchestrationEngine.tsx`, configured entirely
   via props in `frontend/src/components/workflow/pipeline.ts` with our real 6-agent
   pipeline structure and timing (matches `orchestrator/run.py`'s actual concurrent
   dispatch + GIS-runs-last order — see that file's comments). The kit's design tokens
   were merged into `frontend/src/index.css`. Old `WorkflowScene.tsx`/`graph.ts` were
   deleted. Verified rendering correctly in a real browser this session (all nodes
   animate through idle → run → done with real labels, replay button works, no console
   errors, dashboard tab unaffected).

Verified this session: `tsc -b --noEmit` clean, `npm run build` clean, `npm run lint`
clean (one pre-existing warning in `MapView.tsx`, unrelated), predict agent smoke-tested
via direct Python calls and over HTTP, full `orchestrate()` call tested end-to-end with
a real "Is it go for launch tomorrow?" query — predict verdict flowed correctly into
severity scoring and the Gemini-written summary.

## Judgment calls made autonomously (per your "don't ask again" instruction)

- **Predict label ≠ reconstructed scrub history.** No public source exposes real
  per-attempt scrub/delay outcomes, so the label is the launch provider's own
  *published* pre-launch weather-go probability, thresholded at 50%. Disclosed in
  PROVENANCE.md, the README, the agent's `caveat` field, and the UI panel itself.
- **Train/serve feature parity**: dropped `pad_name` and `weather_concerns_raw`-derived
  features from the model — they're launch-pad-specific and not available for an
  arbitrary AOI query. Only the 6 real numeric weather fields are used.
- **NO-GO recall is weak** (~469 rows, ~5% NO-GO, RandomForest recall ~0.20 on NO-GO in
  the held-out test set) — a known, documented limitation, not hidden. See
  `backend/data/launch_weather/metrics.json`.
- **Tutorial step targets** map onto what actually exists in the UI (Map / Watchlist /
  SITREP feed / Predict panel) since "data/info panel" and "summary section" aren't
  separately named sections in the current prototype.
- **No BSERC logo file exists yet** — loading screen uses a particle-assembled text
  wordmark placeholder (`frontend/src/components/intro/ParticleWordmark.tsx`). Swap in
  the real logo there once you have the asset file.
- **Predict agent added as a 7th node** in the workflow visualization graph (alongside
  the original 6), since it's a real new agent in the pipeline now.

## To resume tomorrow

1. **Open it in a real browser and click through everything** — loading screen timing,
   welcome screen, tutorial mascot movement/text, a live query showing the SITREP +
   predict panel, and the Workflow tab's "Run Visualization" button. This is the one
   thing that couldn't be checked this session.
2. Start both servers:
   ```powershell
   cd backend && .\venv\Scripts\python.exe -m uvicorn app.main:app --reload
   cd frontend && npm run dev
   ```
   (Note: port 8000 had a stuck phantom listener mid-session on this machine that
   Windows tools couldn't identify or kill — if `uvicorn --port 8000` fails to bind,
   try a reboot, or run on another port and update `frontend/.env`'s
   `VITE_API_BASE_URL` to match.)
3. If you want to retrain the model with more/fresher data, re-run:
   ```powershell
   cd backend
   .\venv\Scripts\python.exe -m app.agents.predict.build_dataset
   .\venv\Scripts\python.exe -m app.agents.predict.train
   ```
4. Nothing is half-finished — all 4 features are complete per `docs/BUILD_SPEC.md`'s
   definition of done, pending your own visual pass.
