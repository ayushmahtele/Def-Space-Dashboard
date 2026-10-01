import { Scene3D } from "../scene/Scene3D";
import AboutSection from "../../vendor/orchestration-kit/AboutSection";
import type { Feature } from "../../vendor/orchestration-kit/AboutSection";

// Real project description — replaces the orchestration_ui_kit's generic placeholder
// copy per docs/BUILD_SPEC.md and the project's own README.md.
const FEATURES: Feature[] = [
  {
    icon: "bolt",
    title: "Orchestrator",
    body: "Keyword-based intent routing decides which agents are worth calling for a given query instead of always firing all of them — simple and explainable by design.",
  },
  {
    icon: "eye",
    title: "Vision agent",
    body: "NASA GIBS satellite tiles compared with OpenCV pixel-diff change detection to flag visible change at an AOI over time.",
  },
  {
    icon: "grid",
    title: "RAG agent",
    body: "A Chroma vector store over ingested government/press reports, answered with Gemini — every answer is grounded in a real, citable document.",
  },
  {
    icon: "radio",
    title: "Weather agent",
    body: "Current conditions and forecasts from Open-Meteo, no key required — the baseline situational layer for every query.",
  },
  {
    icon: "nodes",
    title: "News agent",
    body: "GNews / NewsData.io headlines scored with an OSINT-style keyword and escalation heuristic to surface what's worth a second look.",
  },
  {
    icon: "globe",
    title: "GIS agent",
    body: "Geofencing and map layers built only from real, derivable geometry — no fabricated pins for individual articles.",
  },
  {
    icon: "shield",
    title: "Translation agent",
    body: "Automatic language detection plus Gemini translation, so a non-English query still routes correctly through every other agent.",
  },
  {
    icon: "target",
    title: "Go / No-Go predict agent",
    body: "A RandomForest + SHAP model trained on real historical launch-weather data, giving a verdict with feature-level reasoning attached — see the Workflow page for how it fits the pipeline.",
  },
];

// Same 3D wordmark scene as the Home page — reused rather than building a second one,
// per the product decision for this page.
export function AboutPage() {
  return (
    <div className="min-h-0 flex-1 overflow-y-auto">
      <Scene3D text="DEF-SPACE" className="h-40 sm:h-48" />
      <AboutSection
        eyebrow="About the system"
        title="Def-Space Multi-Agent Intelligence Dashboard"
        lead="A BSERC Space Education Research Centre project: a defense/space situational-awareness
          platform built by a four-person student team, entirely on free-tier APIs. Every
          key-gated agent reports honestly when it isn't configured instead of faking a result —
          nothing in this pipeline is ever mocked or fabricated. Six agents run behind a single
          orchestrator; a Report agent fuses whatever comes back into one provenance-tagged
          SITREP."
        features={FEATURES}
        style={{ paddingTop: 24 }}
      />
    </div>
  );
}
