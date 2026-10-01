export type Page = "home" | "dashboard" | "workflow" | "model-performance" | "about";

const NAV_ITEMS: { id: Page; label: string }[] = [
  { id: "home", label: "Home" },
  { id: "dashboard", label: "Dashboard" },
  { id: "workflow", label: "Workflow" },
  { id: "model-performance", label: "Model Performance" },
  { id: "about", label: "About" },
];

interface Props {
  geminiConfigured: boolean | null;
  newsConfigured: boolean | null;
  viewMode: "analyst" | "commander";
  onViewModeChange: (mode: "analyst" | "commander") => void;
  page: Page;
  onPageChange: (page: Page) => void;
}

export function Header({ geminiConfigured, newsConfigured, viewMode, onViewModeChange, page, onPageChange }: Props) {
  return (
    <header className="flex flex-wrap items-center justify-between gap-3 border-b border-ops-border bg-ops-panel px-4 py-3 lg:grid lg:grid-cols-[1fr_auto_1fr] lg:gap-4">
      <div className="flex items-center gap-3 justify-self-start">
        <span className="h-2 w-2 shrink-0 animate-pulse rounded-full bg-ops-accent" />
        <h1 className="font-mono text-sm font-semibold tracking-widest text-ops-text">DEF-SPACE</h1>
      </div>

      <nav className="order-last flex w-full items-center gap-1 overflow-x-auto font-mono text-xs lg:order-none lg:w-auto lg:justify-self-center">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            onClick={() => onPageChange(item.id)}
            className={`whitespace-nowrap rounded px-3 py-1.5 uppercase tracking-wide transition-colors ${
              page === item.id
                ? "border border-ops-accent-dim bg-ops-accent/10 text-ops-accent"
                : "border border-transparent text-ops-text-dim hover:text-ops-text"
            }`}
          >
            {item.label}
          </button>
        ))}
      </nav>

      <div className="flex items-center gap-4 justify-self-end">
        <div className="hidden items-center gap-2 font-mono text-[11px] text-ops-text-faint lg:flex">
          <span className={geminiConfigured ? "text-status-ok" : "text-ops-text-faint"}>
            &#9679; Gemini {geminiConfigured ? "on" : "off"}
          </span>
          <span className={newsConfigured ? "text-status-ok" : "text-ops-text-faint"}>
            &#9679; News {newsConfigured ? "on" : "off"}
          </span>
        </div>

        <div className="flex items-center rounded border border-ops-border bg-ops-panel-raised p-0.5 text-xs font-mono">
          {(["analyst", "commander"] as const).map((mode) => (
            <button
              key={mode}
              onClick={() => onViewModeChange(mode)}
              className={`rounded px-2.5 py-1 uppercase tracking-wide ${
                viewMode === mode ? "bg-ops-accent-dim text-ops-text" : "text-ops-text-faint hover:text-ops-text-dim"
              }`}
            >
              {mode}
            </button>
          ))}
        </div>

        <button
          onClick={() => onPageChange("home")}
          title="Back to Home"
          className="flex items-center gap-2 rounded border border-ops-border bg-ops-panel-raised py-1 pl-1.5 pr-2.5 transition-colors hover:border-ops-accent-dim"
        >
          <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded bg-ops-accent-dim">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#e6edf3" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 12h4l2 5 4-12 2 7h6" />
            </svg>
          </span>
          <span className="font-mono text-xs font-semibold tracking-wide text-ops-text">BSERC</span>
        </button>
      </div>
    </header>
  );
}
