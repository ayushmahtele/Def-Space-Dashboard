import type { Sitrep } from "../api/types";
import { SEVERITY_ORDER } from "../lib/severity";
import { SitrepCard } from "./SitrepCard";

export function SitrepFeed({ sitreps, compact = false }: { sitreps: Sitrep[]; compact?: boolean }) {
  if (sitreps.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-ops-border p-8 text-center text-sm text-ops-text-faint">
        No SITREPs yet. Select an AOI and run a query below to generate one.
      </div>
    );
  }

  const sorted = [...sitreps].sort((a, b) => {
    const bySeverity = SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity];
    if (bySeverity !== 0) return bySeverity;
    return new Date(b.generated_at).getTime() - new Date(a.generated_at).getTime();
  });

  return (
    <div className="space-y-3">
      {sorted.map((s, i) => (
        <SitrepCard key={`${s.generated_at}-${i}`} sitrep={s} compact={compact} />
      ))}
    </div>
  );
}
