# Def-Space Multi-Agent Intelligence Dashboard

A multi-agent AI dashboard for defense/space situational awareness. Fuses satellite
imagery, weather, news, maps, and government reports into a single on-demand SITREP
for a defined area of interest (AOI). Built for BSERC's Def-Space AI module using only
free-tier APIs.

This is an **on-demand situational report generator**, not a claim of real-time
monitoring — every SITREP is produced fresh when you submit a query.

## Architecture

```
External data sources (satellite, news, weather, maps, gov reports)
        │
        ▼
Orchestrator (parses query intent, routes to relevant agents, runs them in parallel)
        │
        ├── Vision agent        — NASA GIBS satellite tiles + OpenCV change detection
        ├── RAG agent           — Chroma vector store over ingested gov reports
        ├── Weather agent       — Open-Meteo current + forecast
        ├── News agent          — GNews/NewsData.io + OSINT keyword/escalation scoring
        ├── GIS agent           — geofencing + Leaflet map layers
        └── Translation agent   — langdetect + Gemini translation
        │
        ▼
Report agent (fuses all outputs into one provenance-tagged SITREP + PDF)
        │
        ▼
React dashboard (map, SITREP feed, watchlist, PDF export)
```

## Site structure

Top nav (Home / Dashboard / Workflow / Model Performance / About, centered in the
header, plus a BSERC logo top-right that links back to Home):
`frontend/src/components/Header.tsx`.

- **Home** (`components/pages/HomePage.tsx`) — the app's front door: 3D wordmark scene,
  a short project intro, stat strip, and links into Dashboard/Workflow/About. Replaces
  the old one-time welcome screen — the loading screen still plays once, then drops
  straight into Home.
- **Dashboard** — the original map/watchlist/query/SITREP layout, unchanged.
- **Workflow** — the orchestration pipeline visualization (see below).
- **Model Performance** (`components/pages/ModelPerformancePage.tsx`) — accuracy/
  precision/recall/F1 and a visual confusion matrix for the deployed go/no-go model,
  the train/test split (dates + class counts), a class-imbalance callout, and a
  side-by-side comparison across all 4 candidate classifiers (see below).
- **About** (`components/pages/AboutPage.tsx`) — real project description and an
  8-card breakdown of every agent, built on the ported `AboutSection` component.

Both Home and About share one 3D scene component (`components/scene/Scene3D.tsx`) — a
particle-assembled "DEF-SPACE" wordmark over a starfield, reusing the same technique as
the loading screen's `ParticleWordmark.tsx` rather than a third, separate 3D component.

## Setup

### Backend

Requires **Python 3.12** specifically — Chroma's native dependency has no prebuilt
Windows wheel for 3.13/3.14, and building it from source needs a full C++ toolchain.
If you don't have 3.12: `winget install Python.Python.3.12`.

```powershell
cd backend
py -3.12 -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env    # then fill in whatever keys you have — see below
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Backend runs at `http://127.0.0.1:8000` (interactive docs at `/docs`).

### Frontend

```powershell
cd frontend
npm install
copy .env.example .env
npm run dev
```

Dashboard runs at `http://127.0.0.1:5173`.

## API keys — what works with none, and what each key unlocks

Every agent returns a real, honest result even with zero keys configured — key-gated
agents report `status: "not_configured"` instead of fabricating data. This was a hard
requirement: the demo must never show mocked values anywhere.

| Works with NO key | Needs a key |
|---|---|
| Weather (Open-Meteo) | News — free at [gnews.io](https://gnews.io) or [newsdata.io](https://newsdata.io) |
| GIS / geofencing | RAG answers + embeddings — needs `GEMINI_API_KEY` |
| Vision satellite tiles + change % (NASA GIBS + OpenCV) | Vision's natural-language description — needs `GEMINI_API_KEY` |
| Translation's language detection (langdetect) | Translation's actual translation — needs `GEMINI_API_KEY` |
| | Report agent's LLM-written SITREP prose — falls back to a deterministic rule-based summary built from the same real data if no key is set |

Get a free `GEMINI_API_KEY` at https://aistudio.google.com/apikey (powers Gemini
2.5 Flash for text/vision and `gemini-embedding-001` for RAG). Put keys in
`backend/.env` — see `backend/.env.example` for the full list.

## RAG demo data

`backend/data/reports_raw/` already contains two real PIB (Press Information Bureau
of India) press releases, extracted from their published PDFs, as a seed corpus:
- `pib_defence_budget_2026_27.txt` — Defence in Union Budget 2026-27
- `pib_bro_connecting_places.txt` — Border Roads Organisation feature

Once `GEMINI_API_KEY` is set, ingest them with:

```
POST http://127.0.0.1:8000/agents/rag/ingest
```

Drop more real `.txt` reports (first line = title) in that folder and re-run ingest
to grow the corpus. Never add fabricated report content — the RAG agent's whole point
is grounding answers in real documents it can cite.

## Known scope cuts (documented, not silent)

- **GIS doesn't fabricate per-article news pins.** Free-tier news APIs don't return
  article coordinates, so the map only plots real, derivable geometry: the AOI center
  itself, tagged when Vision or News flags something there. Geocoding individual
  articles would need a paid/heavier NLP service — out of scope for this build.
- **Vision's pixel-diff is a naive OpenCV `absdiff`,** not cloud-masked. On days with
  heavy cloud cover difference between the two satellite passes, "change %" can read
  high even with no ground change — it's real data, just noisy. A production version
  would add a cloud mask before diffing.
- **Translation** is the first agent to cut under time pressure per the original
  brief — it currently only translates the user's query text (via langdetect +
  Gemini), not yet individual foreign-language news/report snippets before they reach
  News/RAG. That per-article pipeline is the natural next extension.
- **The go/no-go predict agent's label isn't a reconstructed scrub history** — public
  launch records don't expose one. It reproduces the launch provider's own published
  pre-launch weather-go call instead. See `backend/data/launch_weather/PROVENANCE.md`.
- **No BSERC logo asset exists yet** — the loading screen assembles a text wordmark
  placeholder from particles (`frontend/src/components/intro/ParticleWordmark.tsx`);
  swap in the real logo there once the asset file is available.

## Intro, tutorial, predictive agent, and workflow visualization

Added on top of the original 6-agent build (see `docs/BUILD_SPEC.md` for the original
brief):

- **Intro sequence** (`frontend/src/components/intro/`) — a one-time particle-assembly
  loading screen followed by a welcome screen, wired in `main.tsx` ahead of `<App />`.
- **Guided tutorial** (`frontend/src/components/tutorial/`) — an original 3D mascot
  (primitive Three.js geometry, not modeled on any existing character) that walks new
  users through Map → Watchlist → SITREP feed → Go/No-Go model result. Skippable,
  replays every visit.
- **Predict agent** (`backend/app/agents/predict/`) — a go/no-go classifier trained on
  real historical SpaceX launch-weather data (see PROVENANCE.md above) with a
  chronological (not random) train/test split and class-balanced weighting for the
  rare NO-GO class. Four classifiers (RandomForest, XGBoost, Logistic Regression,
  Gradient Boosting) are trained on the identical split; whichever scores best on
  NO-GO F1 is deployed (currently RandomForest — see the Model Performance tab for the
  live comparison). Per-prediction SHAP feature-contribution reasoning is surfaced in
  the dashboard (`frontend/src/components/predict/PredictPanel.tsx`), folded into the
  SITREP's claims and severity score, and includes an explicit note that the model is
  applying learned weather-risk patterns to the AOI's live current weather — not
  historical launch data specific to that AOI.
- **Workflow visualization** (`frontend/src/components/workflow/`) — a standalone tab
  (toggle in the header) showing the full data-source → orchestrator → 6-agent (Vision,
  RAG, Weather, News, GIS, Translation) → Report → dashboard pipeline as an animated 3D
  node graph, with the actual last real result shown below once its animation completes.
  Built on the third-party Orchestration UI Kit (`docs/orchestration_ui_kit/`, ported to
  TypeScript at `frontend/src/vendor/orchestration-kit/OrchestrationEngine.tsx`) rather
  than a from-scratch Three.js scene — it's CSS `perspective`/`transform`-based, not
  WebGL. All node labels, edges, and step timing are our real pipeline structure, passed
  in via props from `frontend/src/components/workflow/pipeline.ts` — see that file's
  comments for how the timing maps to `backend/app/orchestrator/run.py`'s actual
  concurrent-dispatch + GIS-runs-last execution order. The kit's design tokens are
  merged into `frontend/src/index.css` alongside the existing Tailwind theme.

## Team work-split (suggested mapping onto this codebase)

- **Member 1 (architecture lead)** — `backend/app/orchestrator/`, `backend/app/agents/report/`,
  `backend/app/main.py`, `backend/app/watchlist.py`
- **Member 2** — `backend/app/agents/vision/`, `backend/app/agents/gis/`
- **Member 3** — `backend/app/agents/rag/`, `backend/app/agents/translation/`
- **Member 4** — `backend/app/agents/news/`, `backend/app/agents/weather/`, `frontend/`

Shared contract everyone depends on: `backend/app/models/schemas.py` (Python) and its
hand-kept mirror `frontend/src/api/types.ts` (TypeScript). Change one, update the other.

## Project layout

```
backend/
  app/
    agents/<name>/{service.py, routes.py}   — one agent, one folder
    orchestrator/{intent.py, run.py, routes.py}
    models/schemas.py                       — shared contract, single source of truth
    core/                                   — config, http client, Gemini wrapper, geo math
    watchlist.py                            — AOI CRUD (flat JSON file)
    main.py                                 — FastAPI app wiring
  data/
    reports_raw/     — .txt gov reports for RAG ingestion
    chroma/           — persisted vector store (gitignored)
    pdf_exports/       — generated SITREP PDFs (gitignored)
frontend/
  src/
    api/{client.ts, types.ts}               — typed fetch wrappers + schema mirror
    components/                             — Header, Watchlist, MapView, QueryBox, SitrepFeed/Card
    lib/severity.ts                          — severity/status colors + agent labels
```
