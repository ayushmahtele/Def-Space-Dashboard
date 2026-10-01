import type { AgentStatus } from "../api/types";
import { AGENT_LABELS, STATUS_STYLES } from "../lib/severity";

export function AgentStatusStrip({ statuses }: { statuses: Record<string, AgentStatus> }) {
  const entries = Object.entries(statuses).filter(([agent]) => agent !== "report");
  return (
    <div className="flex flex-wrap gap-2">
      {entries.map(([agent, status]) => {
        const s = STATUS_STYLES[status];
        return (
          <span
            key={agent}
            title={`${AGENT_LABELS[agent] ?? agent}: ${s.label}`}
            className="inline-flex items-center gap-1.5 rounded border border-ops-border bg-ops-panel px-2 py-1 text-[11px] font-mono text-ops-text-dim"
          >
            <span className={`h-1.5 w-1.5 rounded-full ${s.dot}`} />
            {AGENT_LABELS[agent] ?? agent}
          </span>
        );
      })}
    </div>
  );
}
