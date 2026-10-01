import { useEffect, useState, type FormEvent } from "react";
import type { AOI } from "../api/types";

interface MapPrefill {
  lat: number;
  lon: number;
  name: string;
}

interface Props {
  aois: AOI[];
  activeName: string | null;
  onSelect: (aoi: AOI) => void;
  onAdd: (aoi: AOI) => Promise<void>;
  onRemove: (name: string) => Promise<void>;
  prefill?: MapPrefill | null;
}

export function Watchlist({ aois, activeName, onSelect, onAdd, onRemove, prefill }: Props) {
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: "", lat: "", lon: "", radius_km: "25" });
  const [submitting, setSubmitting] = useState(false);

  // A click on the map passes a new prefill object each time (even for the same
  // spot), so this always re-opens the form with fresh coordinates.
  useEffect(() => {
    if (!prefill) return;
    setForm({
      name: prefill.name,
      lat: prefill.lat.toFixed(4),
      lon: prefill.lon.toFixed(4),
      radius_km: "25",
    });
    setShowForm(true);
  }, [prefill]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const lat = parseFloat(form.lat);
    const lon = parseFloat(form.lon);
    if (!form.name.trim() || Number.isNaN(lat) || Number.isNaN(lon)) return;
    setSubmitting(true);
    try {
      await onAdd({ name: form.name.trim(), lat, lon, radius_km: parseFloat(form.radius_km) || 25 });
      setForm({ name: "", lat: "", lon: "", radius_km: "25" });
      setShowForm(false);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between px-1 pb-2">
        <h2 className="font-mono text-xs font-semibold uppercase tracking-widest text-ops-text-faint">
          AOI Watchlist
        </h2>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="rounded border border-ops-border-strong px-2 py-0.5 text-xs text-ops-accent hover:bg-ops-panel-raised"
        >
          {showForm ? "cancel" : "+ add"}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="mb-3 space-y-2 rounded border border-ops-border bg-ops-panel-raised p-2.5">
          <input
            className="w-full rounded border border-ops-border bg-ops-bg px-2 py-1 text-sm text-ops-text placeholder:text-ops-text-faint focus:border-ops-accent focus:outline-none"
            placeholder="AOI name"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
          <div className="flex gap-2">
            <input
              className="w-1/2 rounded border border-ops-border bg-ops-bg px-2 py-1 text-sm text-ops-text placeholder:text-ops-text-faint focus:border-ops-accent focus:outline-none"
              placeholder="lat"
              value={form.lat}
              onChange={(e) => setForm({ ...form, lat: e.target.value })}
            />
            <input
              className="w-1/2 rounded border border-ops-border bg-ops-bg px-2 py-1 text-sm text-ops-text placeholder:text-ops-text-faint focus:border-ops-accent focus:outline-none"
              placeholder="lon"
              value={form.lon}
              onChange={(e) => setForm({ ...form, lon: e.target.value })}
            />
          </div>
          <input
            className="w-full rounded border border-ops-border bg-ops-bg px-2 py-1 text-sm text-ops-text placeholder:text-ops-text-faint focus:border-ops-accent focus:outline-none"
            placeholder="radius km (default 25)"
            value={form.radius_km}
            onChange={(e) => setForm({ ...form, radius_km: e.target.value })}
          />
          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded bg-ops-accent-dim px-2 py-1.5 text-sm font-medium text-ops-text hover:bg-ops-accent hover:text-ops-bg disabled:opacity-50"
          >
            {submitting ? "saving..." : "Save AOI"}
          </button>
        </form>
      )}

      <div className="flex-1 space-y-1 overflow-y-auto">
        {aois.length === 0 && (
          <p className="px-1 text-xs text-ops-text-faint">No AOIs saved yet.</p>
        )}
        {aois.map((aoi) => (
          <div
            key={aoi.name}
            className={`group flex cursor-pointer items-center justify-between rounded px-2 py-1.5 text-sm ${
              activeName === aoi.name
                ? "border border-ops-accent-dim bg-ops-panel-raised text-ops-text"
                : "border border-transparent text-ops-text-dim hover:bg-ops-panel-raised"
            }`}
            onClick={() => onSelect(aoi)}
          >
            <div>
              <div className="font-medium">{aoi.name}</div>
              <div className="font-mono text-[11px] text-ops-text-faint">
                {aoi.lat.toFixed(3)}, {aoi.lon.toFixed(3)} &middot; {aoi.radius_km}km
              </div>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onRemove(aoi.name);
              }}
              className="hidden shrink-0 rounded px-1.5 text-ops-text-faint hover:text-sev-high group-hover:block"
              title="Remove"
            >
              &times;
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
