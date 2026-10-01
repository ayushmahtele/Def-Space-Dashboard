import { Scene3D } from "../scene/Scene3D";
import type { Page } from "../Header";

const STATS = [
  { value: "6", label: "specialized agents" },
  { value: "5", label: "real-time data sources" },
  { value: "0", label: "mocked data points" },
];

interface HomePageProps {
  onNavigate: (page: Page) => void;
}

// The site's front door: a short professional intro plus the 3D wordmark scene, replacing
// the old one-time welcome screen (which used to play this same copy as a transient
// overlay before dropping straight into the dashboard — see docs/SESSION_HANDOFF.md).
export function HomePage({ onNavigate }: HomePageProps) {
  return (
    <div className="flex min-h-0 flex-1 flex-col items-center overflow-y-auto px-4 py-6">
      <div className="w-full max-w-3xl">
        <Scene3D text="DEF-SPACE" className="h-40 rounded-lg border border-ops-border sm:h-48" />
      </div>

      <div className="mt-6 max-w-2xl text-center">
        <span className="font-mono text-[11px] font-semibold uppercase tracking-[0.3em] text-ops-accent">
          BSERC Space Education Research Centre
        </span>
        <h1 className="mt-4 text-3xl font-semibold tracking-tight text-ops-text sm:text-4xl">
          Multi-Agent Intelligence Dashboard
        </h1>
        <p className="mt-4 text-sm leading-relaxed text-ops-text-dim sm:text-base">
          A defense/space situational-awareness platform that fuses satellite imagery, weather,
          news, maps, and government reports into a single on-demand SITREP for any area of
          interest. Six specialized agents run in parallel behind a keyword-driven orchestrator,
          then hand off to a Report agent that fuses everything into one provenance-tagged
          briefing — built entirely on free-tier APIs, with no mocked or fabricated data anywhere
          in the pipeline.
        </p>

        <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
          <button
            onClick={() => onNavigate("dashboard")}
            className="rounded border border-ops-accent-dim bg-ops-accent/10 px-5 py-2 font-mono text-xs uppercase tracking-wide text-ops-accent transition-colors hover:bg-ops-accent/20"
          >
            Enter Dashboard
          </button>
          <button
            onClick={() => onNavigate("workflow")}
            className="rounded border border-ops-border px-5 py-2 font-mono text-xs uppercase tracking-wide text-ops-text-dim transition-colors hover:border-ops-border-strong hover:text-ops-text"
          >
            View Workflow
          </button>
          <button
            onClick={() => onNavigate("about")}
            className="rounded border border-ops-border px-5 py-2 font-mono text-xs uppercase tracking-wide text-ops-text-dim transition-colors hover:border-ops-border-strong hover:text-ops-text"
          >
            About the System
          </button>
        </div>
      </div>

      <div className="mt-10 grid w-full max-w-2xl grid-cols-3 gap-3 border-y border-ops-border py-5">
        {STATS.map((s) => (
          <div key={s.label} className="text-center">
            <div className="font-mono text-2xl font-semibold text-ops-text">{s.value}</div>
            <div className="mt-1 text-[11px] uppercase tracking-wide text-ops-text-faint">{s.label}</div>
          </div>
        ))}
      </div>

      <div className="mt-8 max-w-xl rounded-lg border border-ops-border bg-ops-panel/60 px-5 py-4 text-center">
        <span className="font-mono text-[10px] font-semibold uppercase tracking-[0.25em] text-ops-accent">
          In development
        </span>
        <p className="mt-2 text-xs leading-relaxed text-ops-text-dim">
          A launch-weather go/no-go model is already live in the pipeline (trained on real
          historical launch and weather data — see the Workflow and Dashboard pages). Additional
          purpose-trained agents are currently being built on top of this same orchestrator and
          will appear here as they ship.
        </p>
      </div>
    </div>
  );
}
