import type { Sitrep } from "../api/types";
import { api } from "../api/client";
import { AGENT_LABELS } from "../lib/severity";
import { SeverityBadge } from "./SeverityBadge";
import { AgentStatusStrip } from "./AgentStatusStrip";

export function SitrepCard({ sitrep, compact = false }: { sitrep: Sitrep; compact?: boolean }) {
  const time = new Date(sitrep.generated_at + "Z").toLocaleString();

  return (
    <article className="rounded-lg border border-ops-border bg-ops-panel p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <SeverityBadge severity={sitrep.severity} />
            {sitrep.alert && (
              <span className="rounded bg-sev-high-bg px-2 py-0.5 text-xs font-mono font-bold text-sev-high animate-pulse">
                ALERT
              </span>
            )}
          </div>
          <h3 className="mt-2 text-sm font-semibold text-ops-text">{sitrep.query}</h3>
          <p className="text-xs text-ops-text-faint">
            {sitrep.aoi?.name ?? "unspecified AOI"} &middot; {time}
          </p>
        </div>
        {sitrep.pdf_url && (
          <a
            href={api.pdfUrl(sitrep.pdf_url)}
            target="_blank"
            rel="noreferrer"
            className="shrink-0 rounded border border-ops-border-strong px-3 py-1.5 text-xs font-mono text-ops-accent hover:bg-ops-panel-raised"
          >
            Export PDF
          </a>
        )}
      </div>

      <p className="mt-3 whitespace-pre-line text-sm leading-relaxed text-ops-text-dim">{sitrep.summary}</p>

      {!compact && sitrep.claims.length > 0 && (
        <div className="mt-4 space-y-1.5">
          {sitrep.claims.map((c, i) => (
            <div
              key={i}
              className="flex items-start gap-2 rounded border border-ops-border/60 bg-ops-panel-raised/50 px-2.5 py-1.5 text-xs"
            >
              <span className="mt-0.5 shrink-0 rounded bg-ops-accent-dim/30 px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wide text-ops-accent">
                {AGENT_LABELS[c.source_agent] ?? c.source_agent}
              </span>
              <span className="text-ops-text-dim">
                {c.text}
                {c.source_detail && (
                  <span className="ml-1 text-ops-text-faint">({c.source_detail})</span>
                )}
              </span>
            </div>
          ))}
        </div>
      )}

      {!compact && (
        <div className="mt-4">
          <AgentStatusStrip statuses={sitrep.agent_statuses} />
        </div>
      )}
    </article>
  );
}
