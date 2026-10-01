import type { AgentStatus, Severity } from "../api/types";

export const SEVERITY_ORDER: Record<Severity, number> = { high: 0, medium: 1, low: 2 };

export const SEVERITY_STYLES: Record<Severity, { text: string; bg: string; label: string }> = {
  high: { text: "text-sev-high", bg: "bg-sev-high-bg", label: "HIGH" },
  medium: { text: "text-sev-medium", bg: "bg-sev-medium-bg", label: "MEDIUM" },
  low: { text: "text-sev-low", bg: "bg-sev-low-bg", label: "LOW" },
};

export const STATUS_STYLES: Record<AgentStatus, { dot: string; label: string }> = {
  ok: { dot: "bg-status-ok", label: "ok" },
  not_configured: { dot: "bg-status-not-configured", label: "no key" },
  error: { dot: "bg-status-error", label: "error" },
  skipped: { dot: "bg-status-skipped", label: "skipped" },
};

export const AGENT_LABELS: Record<string, string> = {
  vision: "Vision",
  rag: "RAG / Reports",
  weather: "Weather",
  news: "News",
  gis: "GIS",
  translation: "Translation",
  report: "Report",
  predict: "Go/No-Go Model",
};
