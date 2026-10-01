import { useEffect, useMemo, useState } from "react";
import { MapContainer, TileLayer, Circle, CircleMarker, Popup, useMap, useMapEvent } from "react-leaflet";
import type { AOI, GeoFeature } from "../api/types";

const LAYER_COLORS: Record<string, string> = {
  aoi: "#22d3ee",
  news: "#ef4444",
  satellite_change: "#f59e0b",
  reports: "#a78bfa",
};

function Recenter({ lat, lon }: { lat: number; lon: number }) {
  const map = useMap();
  // Only snap the view when the AOI itself changes — not on every re-render
  // (typing in the query box, adding a SITREP, etc. all re-render this
  // component too, and re-centering on each of those fought the user's own
  // pan/zoom, making the map feel frozen/unresponsive).
  useEffect(() => {
    map.setView([lat, lon], map.getZoom() < 4 ? 8 : map.getZoom());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lat, lon]);
  return null;
}

function ClickCapture({ onClick }: { onClick: (lat: number, lon: number) => void }) {
  useMapEvent("click", (e) => onClick(e.latlng.lat, e.latlng.lng));
  return null;
}

export function MapView({
  aoi,
  features,
  onMapClick,
}: {
  aoi: AOI | null;
  features: GeoFeature[];
  onMapClick?: (lat: number, lon: number) => void;
}) {
  const layers = useMemo(() => Array.from(new Set(features.map((f) => f.layer))), [features]);
  const [visible, setVisible] = useState<Set<string>>(new Set(["aoi", "news", "satellite_change", "reports"]));

  function toggle(layer: string) {
    setVisible((prev) => {
      const next = new Set(prev);
      next.has(layer) ? next.delete(layer) : next.add(layer);
      return next;
    });
  }

  const center: [number, number] = aoi ? [aoi.lat, aoi.lon] : [20, 0];

  return (
    <div className="relative h-full w-full overflow-hidden rounded-lg border border-ops-border">
      <MapContainer center={center} zoom={aoi ? 8 : 2} className="h-full w-full" scrollWheelZoom>
        <TileLayer
          attribution='Tiles &copy; Esri'
          url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}"
        />
        {aoi && <Recenter lat={aoi.lat} lon={aoi.lon} />}
        {onMapClick && <ClickCapture onClick={onMapClick} />}
        {aoi && (
          <Circle
            center={[aoi.lat, aoi.lon]}
            radius={aoi.radius_km * 1000}
            pathOptions={{ color: LAYER_COLORS.aoi, fillOpacity: 0.05, weight: 1.5 }}
          />
        )}
        {features
          .filter((f) => visible.has(f.layer))
          .map((f) => (
            <CircleMarker
              key={f.id}
              center={[f.lat, f.lon]}
              radius={f.layer === "aoi" ? 5 : 8}
              pathOptions={{
                color: LAYER_COLORS[f.layer] ?? "#e6edf3",
                fillColor: LAYER_COLORS[f.layer] ?? "#e6edf3",
                fillOpacity: 0.85,
                weight: 2,
              }}
            >
              <Popup>
                <div className="font-mono text-xs">
                  <div className="font-semibold">{f.label}</div>
                  <div className="text-ops-text-faint">layer: {f.layer}</div>
                  <div className="text-ops-text-faint">source: {f.source_agent}</div>
                </div>
              </Popup>
            </CircleMarker>
          ))}
      </MapContainer>

      {onMapClick && (
        <div className="absolute bottom-2 left-2 z-[1000] rounded border border-ops-border bg-ops-panel/90 px-2 py-1 text-[11px] text-ops-text-faint backdrop-blur">
          Click the map to add an AOI at that location
        </div>
      )}

      {layers.length > 0 && (
        <div className="absolute right-2 top-2 z-[1000] rounded border border-ops-border bg-ops-panel/90 p-2 text-xs backdrop-blur">
          <div className="mb-1 font-mono uppercase tracking-wide text-ops-text-faint">Layers</div>
          {layers.map((layer) => (
            <label key={layer} className="flex cursor-pointer items-center gap-1.5 py-0.5 text-ops-text-dim">
              <input
                type="checkbox"
                checked={visible.has(layer)}
                onChange={() => toggle(layer)}
                className="accent-ops-accent"
              />
              <span className="h-2 w-2 rounded-full" style={{ background: LAYER_COLORS[layer] ?? "#e6edf3" }} />
              {layer}
            </label>
          ))}
        </div>
      )}
    </div>
  );
}
