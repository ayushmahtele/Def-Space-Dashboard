import type { AOI, ModelPerformanceResponse, OrchestrateResponse } from "./types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`${init?.method ?? "GET"} ${path} failed: ${res.status} ${body}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string; gemini_configured: boolean; news_configured: boolean }>("/health"),

  listWatchlist: () => request<AOI[]>("/watchlist"),
  addToWatchlist: (aoi: AOI) =>
    request<AOI[]>("/watchlist", { method: "POST", body: JSON.stringify(aoi) }),
  removeFromWatchlist: (name: string) =>
    request<AOI[]>(`/watchlist/${encodeURIComponent(name)}`, { method: "DELETE" }),

  orchestrate: (query: string, aoi: AOI) =>
    request<OrchestrateResponse>("/orchestrate", {
      method: "POST",
      body: JSON.stringify({ query, aoi }),
    }),

  pdfUrl: (pdfPath: string) => `${BASE_URL}${pdfPath}`,

  modelPerformance: () => request<ModelPerformanceResponse>("/agents/predict/model-performance"),
};
