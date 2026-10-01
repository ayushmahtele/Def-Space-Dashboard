# Build Spec — Intro Experience, Guided Tutorial, Predictive Agent, Workflow Visualization

Before writing any code, ask clarifying questions about anything below that is ambiguous
or where you'd otherwise have to guess. Do not assume defaults for design choices, data
shapes, or file locations — ask first. Once answered, proceed autonomously and keep
working, iterating, and self-correcting until every item below is fully working. Do not
stop to ask permission for routine actions (installing packages, creating files, running
the dev server) — only ask about design/product decisions you're unsure of.

## Project context

This is the Def-Space Multi-Agent Intelligence Dashboard — an existing working prototype
(React + Vite + Tailwind frontend, FastAPI backend, all agent APIs already wired and
functional: Vision, RAG, Weather, News, GIS, Translation, Report agent, orchestrator). Do
not break any existing functionality. The goal now is to add a professional intro
experience, a guided tutorial, a workflow visualization, and a new predictive model agent.

### 1. Loading screen

- Plays once when the site first loads
- Uses our BSERC Space Education Research Centre logo (ask where the logo asset file is
  if it isn't found in the project)
- 3D animated reveal of the logo (rotation, particle assembly, or similar — reuse the
  same Three.js approach as our existing `ParticleLoader.jsx` if present in the codebase)
- Lasts roughly 2-3 seconds, then transitions into a short welcome screen

### 2. Welcome / intro

- 2-3 seconds of intro text (ask for the exact welcome copy/lines, or propose 2-3
  options to pick from)
- A short 3D animation accompanying the intro text (can reuse or extend the loading
  screen's 3D scene)
- Auto-transitions into the main dashboard after the intro completes

### 3. Guided tutorial — animated 3D mascot bot

- An animated 3D character/mascot (ask if there's a specific mascot design/model, or
  whether to generate a simple original 3D character — do not use any copyrighted
  character)
- On first load, the mascot walks the user through the dashboard step by step:
  - Map opens → mascot says something like "Select any city whose AOI you want to know"
  - User selects a location → mascot moves toward the data/info panel and explains it
    (relevant data, info tips, fun facts)
  - Mascot moves toward the summary section and explains what it shows
  - Mascot moves toward the model/agent result section and explains what it shows
- Mascot should visually point/move toward each feature as it's introduced, not just
  appear statically
- Ask whether the tutorial should be skippable and whether it should only show on first
  visit (e.g. via local state) or every time

### 4. Predictive model agent ("go / no-go")

- Trained on real historical labeled data (ask: where is this dataset located, what are
  the input features, what is the exact label/target, and how many rows/samples are
  there — do not assume any of this)
- Once data details are confirmed, build an appropriately-scoped model (likely a tabular
  classifier such as XGBoost or RandomForest — confirm architecture before committing to
  it)
- The model's output must include not just a verdict but the reasoning/feature
  contributions behind it, so the Report agent can explain why
- Wire its output into the existing agent/report pipeline as a new section in the
  dashboard

### 5. Orchestration workflow visualization (3D, Three.js)

- A 3D Three.js scene (reuse the visual language of our existing `CandlestickHero.jsx`
  if present) showing all agents and data sources as connected nodes
- Nodes: data sources (satellite, news, weather, maps, gov reports) → orchestrator → 6
  agents (Vision, RAG, Weather, News, GIS, Translation) → Report agent → dashboard
- Animate data/energy flowing along the connections between nodes when a query runs, so
  it visually reads as "everything working together"
- After the animation completes, display the actual result from the model/report agent
  below or alongside the visualization
- Ask whether this visualization should be a standalone section/tab, or embedded within
  the existing agent-result section

## General constraints

- Don't touch or break the existing map, AOI watchlist, data panel, or summary
  functionality — only add to it
- Match the existing dark tactical UI theme already in the prototype
- Keep all new components isolated (new files/folders) so they're easy for teammates to
  review individually
- After each major piece (loading screen, tutorial, model agent, workflow viz) is
  working, pause and summarize what was built and how to test it, before moving to the
  next piece

## Definition of done

All four features above are implemented, functional, visually consistent with the
existing dashboard theme, and do not regress any existing prototype functionality. Keep
working, testing, and self-correcting until this is true.
