import type { PredictResult } from "../../api/types";

const FEATURE_LABELS: Record<string, string> = {
  temp_max_c: "Max temp (°C)",
  temp_min_c: "Min temp (°C)",
  precipitation_mm: "Precipitation (mm)",
  windspeed_max_kmh: "Max windspeed (km/h)",
  windgusts_max_kmh: "Max wind gusts (km/h)",
  cloudcover_mean_pct: "Mean cloud cover (%)",
};

export function PredictPanel({ result }: { result: PredictResult }) {
  const isGo = result.verdict === "GO";
  const maxAbsContribution = Math.max(0.001, ...result.feature_contributions.map((c) => Math.abs(c.contribution)));

  return (
    <div data-tutorial="predict" className="rounded-lg border border-ops-border bg-ops-panel p-4">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-xs font-mono uppercase tracking-wide text-ops-text-dim">Go/No-Go Model</h3>
        <span
          className={`rounded px-2.5 py-1 text-sm font-mono font-bold ${
            isGo ? "bg-sev-low-bg text-sev-low" : "bg-sev-high-bg text-sev-high"
          }`}
        >
          {result.verdict}
        </span>
      </div>

      <p className="mt-2 text-xs text-ops-text-dim">
        {result.aoi_name} &middot; {result.date} &middot; {(result.go_probability * 100).toFixed(0)}% go probability
      </p>

      {result.methodology_note && (
        <p className="mt-2 rounded border border-ops-accent-dim/40 bg-ops-accent/5 px-2.5 py-2 text-[11px] leading-relaxed text-ops-text-dim">
          {result.methodology_note}
        </p>
      )}

      <div className="mt-3 space-y-1.5">
        {result.feature_contributions.map((c) => {
          const pushesGo = c.contribution >= 0;
          const widthPct = (Math.abs(c.contribution) / maxAbsContribution) * 100;
          return (
            <div key={c.feature} className="flex items-center gap-2 text-xs">
              <span className="w-40 shrink-0 truncate text-ops-text-dim">
                {FEATURE_LABELS[c.feature] ?? c.feature}
              </span>
              <span className="w-14 shrink-0 text-right font-mono text-ops-text-faint">{c.value}</span>
              <div className="h-2 flex-1 overflow-hidden rounded bg-ops-panel-raised">
                <div
                  className={`h-full ${pushesGo ? "bg-sev-low" : "bg-sev-high"}`}
                  style={{ width: `${widthPct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      <p className="mt-3 text-[11px] leading-relaxed text-ops-text-faint">{result.caveat}</p>
    </div>
  );
}
