import type { Severity } from "../api/types";
import { SEVERITY_STYLES } from "../lib/severity";

export function SeverityBadge({ severity }: { severity: Severity }) {
  const s = SEVERITY_STYLES[severity];
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded px-2 py-0.5 text-xs font-mono font-semibold tracking-wide ${s.text} ${s.bg}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${s.text.replace("text-", "bg-")}`} />
      {s.label}
    </span>
  );
}
