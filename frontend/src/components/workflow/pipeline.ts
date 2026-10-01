import type { EngineEdge, EngineLayer, ScriptStep } from "../../vendor/orchestration-kit/OrchestrationEngine";

// Real structure of this project's pipeline (see backend/app/orchestrator/run.py and
// intent.py) — not the OrchestrationEngine kit's generic placeholder content.
// Layer order follows docs/BUILD_SPEC.md item 5: data sources -> orchestrator -> the
// 6 always-present agents (Vision, RAG, Weather, News, GIS, Translation) -> Report
// agent -> dashboard. The predict (go/no-go) agent is intentionally left out here: it's
// a later, keyword-triggered addition (see intent.py's PREDICT_KEYWORDS) on top of the
// spec's original 6-agent pipeline, not one of the 6 named in the spec for this diagram.
export const PIPELINE_LAYERS: EngineLayer[] = [
  [
    { id: "src-sat", label: "Satellite", sub: "NASA GIBS tiles" },
    { id: "src-news", label: "News", sub: "GNews / NewsData.io" },
    { id: "src-weather", label: "Weather", sub: "Open-Meteo" },
    { id: "src-maps", label: "Maps", sub: "Leaflet / OSM" },
    { id: "src-gov", label: "Gov reports", sub: "PIB press releases" },
  ],
  [{ id: "orch", label: "Orchestrator", sub: "keyword intent routing" }],
  [
    { id: "agent-vision", label: "Vision", sub: "GIBS + OpenCV diff", outs: ["out-vision"] },
    { id: "agent-rag", label: "RAG", sub: "Chroma + Gemini", outs: ["out-rag"] },
    { id: "agent-weather", label: "Weather", sub: "current + forecast", outs: ["out-weather"] },
    { id: "agent-news", label: "News", sub: "OSINT escalation score", outs: ["out-news"] },
    { id: "agent-gis", label: "GIS", sub: "geofencing + map pins", outs: ["out-gis"] },
    { id: "agent-translation", label: "Translation", sub: "langdetect + Gemini", outs: ["out-translation"] },
  ],
  [{ id: "report", label: "Report agent", sub: "fuses claims + severity", outs: ["out-report"] }],
  [{ id: "dashboard", label: "Dashboard", sub: "SITREP, map, watchlist" }],
];

export const PIPELINE_EDGES: EngineEdge[] = [
  ["src-sat", "orch"],
  ["src-news", "orch"],
  ["src-weather", "orch"],
  ["src-maps", "orch"],
  ["src-gov", "orch"],

  ["orch", "agent-vision"],
  ["orch", "agent-rag"],
  ["orch", "agent-weather"],
  ["orch", "agent-news"],
  ["orch", "agent-gis"],
  ["orch", "agent-translation"],

  ["agent-vision", "report"],
  ["agent-rag", "report"],
  ["agent-weather", "report"],
  ["agent-news", "report"],
  ["agent-gis", "report"],
  ["agent-translation", "report"],

  ["report", "dashboard"],
];

// Kept within the app's cyan/green ops-room palette (see index.css) rather than the
// kit's original purple/pink defaults, so the animation reads as part of the same
// product, not a visually distinct "engine room".
const C = {
  purple: "#22d3ee",
  blue: "#38bdf8",
  cyan: "#7dd3fc",
  pink: "#f59e0b",
  amber: "#f59e0b",
  green: "#22c55e",
  greenSoft: "#86efac",
};

// Timed to mirror how backend/app/orchestrator/run.py actually executes a query:
// weather/news/vision/rag/translation are dispatched together and run concurrently via
// asyncio.gather (so their packets/outs fire close together, not agent-by-agent), and
// GIS deliberately runs last because it plots pins built from vision's and news's
// results (fetch_gis is only called once those two are in hand).
export const PIPELINE_SCRIPT: ScriptStep[] = [
  { at: 300, active: ["orch"], log: ["[orchestrator] query received · resolving intent", C.purple] },
  {
    at: 900,
    active: ["src-sat", "src-news", "src-weather", "src-maps", "src-gov"],
    packets: [
      ["src-sat", "orch", C.blue],
      ["src-news", "orch", C.blue],
      ["src-weather", "orch", C.blue],
      ["src-maps", "orch", C.blue],
      ["src-gov", "orch", C.blue],
    ],
  },
  {
    at: 1700,
    done: ["src-sat", "src-news", "src-weather", "src-maps", "src-gov"],
    log: ["[intent] baseline agents selected → weather, news, gis", C.cyan],
  },
  {
    at: 2300,
    active: ["agent-weather", "agent-news", "agent-vision", "agent-rag", "agent-translation"],
    packets: [
      ["orch", "agent-weather", C.cyan],
      ["orch", "agent-news", C.cyan],
      ["orch", "agent-vision", C.cyan],
      ["orch", "agent-rag", C.cyan],
      ["orch", "agent-translation", C.cyan],
    ],
    log: ["[agents] running concurrently · asyncio.gather", "#60a5fa"],
  },
  { at: 4200, out: ["out-weather", "fetched → <b>forecast + current</b>"], done: ["agent-weather"] },
  { at: 4700, out: ["out-translation", "detected → <b>en, no translation needed</b>"], done: ["agent-translation"] },
  { at: 5300, out: ["out-rag", "matched → <b>2 reports</b>"], done: ["agent-rag"] },
  { at: 5900, out: ["out-vision", "change → <b>0.0% diff</b>"], done: ["agent-vision"] },
  {
    at: 6500,
    out: ["out-news", "scored → <b>escalation index</b>"],
    done: ["agent-news"],
    log: ["[gis] vision + news complete · fetch_gis can run now", C.pink],
  },
  {
    at: 7100,
    active: ["agent-gis"],
    packets: [["orch", "agent-gis", C.amber]],
    log: ["[gis] plotting AOI geometry from vision/news findings", C.amber],
  },
  { at: 8300, out: ["out-gis", "plotted → <b>AOI pins</b>"], done: ["agent-gis", "orch"] },
  {
    at: 8900,
    active: ["report"],
    packets: [
      ["agent-vision", "report", C.cyan],
      ["agent-rag", "report", C.cyan],
      ["agent-weather", "report", C.cyan],
      ["agent-news", "report", C.cyan],
      ["agent-gis", "report", C.amber],
      ["agent-translation", "report", C.cyan],
    ],
    log: ["[report] fusing claims + severity score", C.green],
  },
  {
    at: 10600,
    out: ["out-report", "SITREP → <b>ready</b>"],
    done: ["report"],
    packets: [["report", "dashboard", C.green]],
    tilt: true,
  },
  { at: 11400, active: ["dashboard"], log: ["[dashboard] rendering SITREP, map pins, watchlist", C.green] },
  { at: 12200, done: ["dashboard"], log: ["[orchestrator] cycle complete", C.greenSoft] },
];

export const PIPELINE_TOTAL_MS = 12200;
