// Mirrors backend/app/models/schemas.py — keep these two files in sync by hand.

export type AgentName = "vision" | "rag" | "weather" | "news" | "gis" | "translation" | "report" | "predict";
export type AgentStatus = "ok" | "not_configured" | "error" | "skipped";
export type Severity = "low" | "medium" | "high";

export interface AOI {
  name: string;
  lat: number;
  lon: number;
  radius_km: number;
  notes?: string | null;
}

export interface AgentEnvelope<T = unknown> {
  agent: AgentName;
  status: AgentStatus;
  data: T | null;
  error: string | null;
  fetched_at: string;
}

export interface ForecastEntry {
  time: string;
  temperature_c: number | null;
  cloud_cover_pct: number | null;
  visibility_m: number | null;
  precipitation_mm: number | null;
}

export interface WeatherResult {
  aoi_name: string;
  latitude: number;
  longitude: number;
  temperature_c: number;
  windspeed_kmh: number;
  winddirection_deg: number;
  weathercode: number;
  is_day: boolean;
  forecast: ForecastEntry[];
  operational_flag: boolean;
  flag_reason: string | null;
}

export interface NewsArticle {
  title: string;
  url: string;
  source: string;
  published_at: string | null;
  snippet: string | null;
  keywords_matched: string[];
  escalation_score: number;
}

export interface NewsResult {
  query: string;
  articles: NewsArticle[];
  overall_escalation: number;
  escalation_flag: boolean;
}

export interface GeoFeature {
  id: string;
  lat: number;
  lon: number;
  label: string;
  layer: "aoi" | "news" | "weather" | "reports" | "satellite_change" | string;
  source_agent: AgentName;
  severity: Severity | null;
}

export interface GeofenceStatus {
  feature_id: string;
  inside_zone: boolean;
  distance_km: number;
}

export interface GISResult {
  aoi: AOI;
  features: GeoFeature[];
  geofence_statuses: GeofenceStatus[];
}

export interface VisionResult {
  aoi_name: string;
  tile_before_url: string | null;
  tile_after_url: string | null;
  date_before: string | null;
  date_after: string | null;
  change_detected: boolean | null;
  change_percentage: number | null;
  description: string | null;
  confidence: number | null;
}

export interface RagSource {
  document: string;
  section: string | null;
  score: number;
}

export interface RagResult {
  query: string;
  answer: string;
  sources: RagSource[];
}

export interface TranslationResult {
  original_text: string;
  detected_language: string;
  translated_text: string;
}

export interface FeatureContribution {
  feature: string;
  value: number;
  contribution: number;
}

export interface PredictResult {
  aoi_name: string;
  latitude: number;
  longitude: number;
  date: string;
  verdict: "GO" | "NO-GO";
  go_probability: number;
  weather_inputs: Record<string, number>;
  feature_contributions: FeatureContribution[];
  caveat: string;
  methodology_note: string;
}

export interface ClassMetrics {
  precision: number;
  recall: number;
  f1_score: number;
  support: number;
}

export interface ModelMetrics {
  key: string;
  display_name: string;
  accuracy: number;
  go: ClassMetrics;
  no_go: ClassMetrics;
  macro_f1: number;
  confusion_matrix: number[][];
  is_deployed: boolean;
}

export interface DatasetSplitInfo {
  total_rows: number;
  train_rows: number;
  test_rows: number;
  train_date_start: string;
  train_date_end: string;
  test_date_start: string;
  test_date_end: string;
  train_go: number;
  train_no_go: number;
  test_go: number;
  test_no_go: number;
  split_method: string;
}

export interface ModelPerformanceResponse {
  dataset: DatasetSplitInfo;
  models: ModelMetrics[];
  deployed_model_key: string;
  selection_rule: string;
  imbalance_note: string;
}

export interface ProvenancedClaim {
  text: string;
  source_agent: AgentName;
  source_detail: string | null;
}

export interface Sitrep {
  query: string;
  aoi: AOI | null;
  generated_at: string;
  severity: Severity;
  summary: string;
  claims: ProvenancedClaim[];
  alert: boolean;
  agent_statuses: Record<string, AgentStatus>;
  pdf_url: string | null;
}

export interface OrchestrateResponse {
  sitrep: Sitrep;
  raw: Record<string, AgentEnvelope>;
}
