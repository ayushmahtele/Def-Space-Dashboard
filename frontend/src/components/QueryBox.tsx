import { useState, type FormEvent } from "react";

interface Props {
  disabled: boolean;
  disabledReason?: string;
  onSubmit: (query: string) => Promise<void>;
}

const EXAMPLES = [
  "Current conditions and any elevated activity in this AOI",
  "Any satellite change or construction visible recently?",
  "Summarize relevant government reports for this region",
];

export function QueryBox({ disabled, disabledReason, onSubmit }: Props) {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!query.trim() || disabled) return;
    setLoading(true);
    try {
      await onSubmit(query.trim());
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-lg border border-ops-border bg-ops-panel p-3">
      <div className="flex gap-2">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={disabled || loading}
          placeholder={disabled ? disabledReason ?? "Select an AOI first" : "Ask about this AOI..."}
          className="flex-1 rounded border border-ops-border bg-ops-bg px-3 py-2 text-sm text-ops-text placeholder:text-ops-text-faint focus:border-ops-accent focus:outline-none disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={disabled || loading || !query.trim()}
          className="rounded bg-ops-accent-dim px-4 py-2 text-sm font-medium text-ops-text hover:bg-ops-accent hover:text-ops-bg disabled:opacity-40"
        >
          {loading ? "Running agents..." : "Generate SITREP"}
        </button>
      </div>
      <div className="mt-2 flex flex-wrap gap-1.5">
        {EXAMPLES.map((ex) => (
          <button
            type="button"
            key={ex}
            disabled={disabled || loading}
            onClick={() => setQuery(ex)}
            className="rounded border border-ops-border px-2 py-0.5 text-[11px] text-ops-text-faint hover:border-ops-border-strong hover:text-ops-text-dim disabled:opacity-40"
          >
            {ex}
          </button>
        ))}
      </div>
    </form>
  );
}
