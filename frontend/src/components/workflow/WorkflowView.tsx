import { useEffect, useState } from "react";
import type { PredictResult, Sitrep } from "../../api/types";
import OrchestrationEngine from "../../vendor/orchestration-kit/OrchestrationEngine";
import { PIPELINE_LAYERS, PIPELINE_EDGES, PIPELINE_SCRIPT, PIPELINE_TOTAL_MS } from "./pipeline";
import { SitrepCard } from "../SitrepCard";
import { PredictPanel } from "../predict/PredictPanel";

interface WorkflowViewProps {
  latestSitrep: Sitrep | null;
  predictResult: PredictResult | null;
}

// Standalone visualization of how a query moves through the system: data sources ->
// orchestrator -> the 6 core agents (Vision, RAG, Weather, News, GIS, Translation) ->
// Report agent -> dashboard, via the Orchestration UI Kit's 3D engine (CSS
// perspective/transform, not WebGL — see docs/orchestration_ui_kit). The engine
// auto-plays on mount and has its own "Replay run" trigger built in; the real last
// result is revealed below once that initial run's timeline (PIPELINE_TOTAL_MS)
// finishes, then stays visible across replays.
export function WorkflowView({ latestSitrep, predictResult }: WorkflowViewProps) {
  const [showResult, setShowResult] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setShowResult(true), PIPELINE_TOTAL_MS + 500);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-3 p-3">
      <h2 className="text-xs font-mono uppercase tracking-wide text-ops-text-dim">Orchestration Workflow</h2>

      <div className="shrink-0 overflow-hidden rounded-lg border border-ops-border">
        <OrchestrationEngine
          tilt={34}
          layers={PIPELINE_LAYERS}
          edges={PIPELINE_EDGES}
          script={PIPELINE_SCRIPT}
          headerLabel="Def-Space orchestration pipeline · live"
        />
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto pr-1">
        {!showResult && !latestSitrep && (
          <p className="text-xs text-ops-text-faint">
            Run a query from the Dashboard tab to see a real SITREP appear here once the pipeline animation above finishes.
          </p>
        )}
        {showResult && latestSitrep && (
          <div className="space-y-3">
            <SitrepCard sitrep={latestSitrep} />
            {predictResult && <PredictPanel result={predictResult} />}
          </div>
        )}
      </div>
    </div>
  );
}
