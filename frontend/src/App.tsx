import { useEffect, useState } from "react";
import { api } from "./api/client";
import type { AOI, GeoFeature, GISResult, PredictResult, Sitrep } from "./api/types";
import { Header, type Page } from "./components/Header";
import { Watchlist } from "./components/Watchlist";
import { MapView } from "./components/MapView";
import { QueryBox } from "./components/QueryBox";
import { SitrepFeed } from "./components/SitrepFeed";
import { TutorialOverlay } from "./components/tutorial/TutorialOverlay";
import { PredictPanel } from "./components/predict/PredictPanel";
import { WorkflowView } from "./components/workflow/WorkflowView";
import { HomePage } from "./components/pages/HomePage";
import { AboutPage } from "./components/pages/AboutPage";
import { ModelPerformancePage } from "./components/pages/ModelPerformancePage";

export default function App() {
  const [aois, setAois] = useState<AOI[]>([]);
  const [activeAoi, setActiveAoi] = useState<AOI | null>(null);
  const [sitreps, setSitreps] = useState<Sitrep[]>([]);
  const [features, setFeatures] = useState<GeoFeature[]>([]);
  const [predictResult, setPredictResult] = useState<PredictResult | null>(null);
  const [health, setHealth] = useState<{ gemini_configured: boolean; news_configured: boolean } | null>(null);
  const [viewMode, setViewMode] = useState<"analyst" | "commander">("analyst");
  const [error, setError] = useState<string | null>(null);
  const [mapPrefill, setMapPrefill] = useState<{ lat: number; lon: number; name: string } | null>(null);
  const [showTutorial, setShowTutorial] = useState(false);
  const [tutorialSeen, setTutorialSeen] = useState(false);
  const [page, setPage] = useState<Page>("home");

  // The guided tutorial only makes sense once the Dashboard's own elements exist to
  // anchor to (map, watchlist, query box, SITREP feed) — Home is now the first screen,
  // so trigger it the first time the user actually reaches Dashboard instead of on
  // app mount. Still skippable, still shows again each time you land on Dashboard
  // fresh in a new session (no persistent "seen it" storage, per the original decision).
  useEffect(() => {
    if (page === "dashboard" && !tutorialSeen) {
      setShowTutorial(true);
      setTutorialSeen(true);
    }
  }, [page, tutorialSeen]);

  useEffect(() => {
    api
      .listWatchlist()
      .then((list) => {
        setAois(list);
        if (list.length > 0) setActiveAoi(list[0]);
      })
      .catch(() => setError("Could not reach the backend. Is uvicorn running on port 8000?"));
    api.health().then(setHealth).catch(() => setHealth(null));
  }, []);

  async function handleAdd(aoi: AOI) {
    const updated = await api.addToWatchlist(aoi);
    setAois(updated);
    setActiveAoi(aoi);
  }

  async function handleRemove(name: string) {
    const updated = await api.removeFromWatchlist(name);
    setAois(updated);
    if (activeAoi?.name === name) setActiveAoi(updated[0] ?? null);
  }

  async function handleMapClick(lat: number, lon: number) {
    let name = `${lat.toFixed(3)}, ${lon.toFixed(3)}`;
    try {
      // Nominatim (OSM) reverse geocoding — free, no key, ~1 req/sec.
      const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lon}&zoom=10`);
      if (res.ok) {
        const data = await res.json();
        const addr = data.address ?? {};
        name = addr.city || addr.town || addr.county || addr.state || data.display_name?.split(",")[0] || name;
      }
    } catch {
      // Offline or rate-limited — fall back to raw coordinates as the name.
    }
    setMapPrefill({ lat, lon, name });
  }

  async function handleQuery(query: string) {
    if (!activeAoi) return;
    setError(null);
    try {
      const res = await api.orchestrate(query, activeAoi);
      setSitreps((prev) => [res.sitrep, ...prev]);
      const gis = res.raw["gis"]?.data as GISResult | undefined;
      setFeatures(gis?.features ?? []);
      const predict = res.raw["predict"];
      setPredictResult(predict?.status === "ok" ? (predict.data as PredictResult) : null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Query failed");
    }
  }

  return (
    <div className="flex h-screen flex-col">
      <Header
        geminiConfigured={health?.gemini_configured ?? null}
        newsConfigured={health?.news_configured ?? null}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        page={page}
        onPageChange={setPage}
      />

      {error && page === "dashboard" && (
        <div className="border-b border-sev-high/30 bg-sev-high-bg px-4 py-2 text-xs text-sev-high">{error}</div>
      )}

      {page === "home" && <HomePage onNavigate={setPage} />}
      {page === "about" && <AboutPage />}
      {page === "model-performance" && <ModelPerformancePage />}

      {page === "dashboard" && (
        <div className="flex min-h-0 flex-1">
          <aside data-tutorial="watchlist" className="w-64 shrink-0 border-r border-ops-border bg-ops-panel/40 p-3">
            <Watchlist
              aois={aois}
              activeName={activeAoi?.name ?? null}
              onSelect={setActiveAoi}
              onAdd={handleAdd}
              onRemove={handleRemove}
              prefill={mapPrefill}
            />
          </aside>

          <main className="flex min-w-0 flex-1 gap-3 p-3">
            <div data-tutorial="map" className="w-1/2 min-w-0">
              <MapView aoi={activeAoi} features={features} onMapClick={handleMapClick} />
            </div>

            <div className="flex w-1/2 min-w-0 flex-col gap-3">
              <div data-tutorial="query">
                <QueryBox
                  disabled={!activeAoi}
                  disabledReason="Select or add an AOI in the watchlist first"
                  onSubmit={handleQuery}
                />
              </div>
              <div data-tutorial="sitrep" className="min-h-0 flex-1 overflow-y-auto pr-1">
                <SitrepFeed sitreps={sitreps} compact={viewMode === "commander"} />
                {predictResult && (
                  <div className="mt-3">
                    <PredictPanel result={predictResult} />
                  </div>
                )}
              </div>
            </div>
          </main>
        </div>
      )}

      {page === "workflow" && (
        <WorkflowView latestSitrep={sitreps[0] ?? null} predictResult={predictResult} />
      )}

      {showTutorial && page === "dashboard" && <TutorialOverlay onDismiss={() => setShowTutorial(false)} />}
    </div>
  );
}
