import { useEffect, useState } from "react";
import { api } from "../../api/client";
import type { ModelMetrics, ModelPerformanceResponse } from "../../api/types";

function MetricBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="flex items-center gap-2 text-[11px]">
      <span className="w-16 shrink-0 text-ops-text-dim">{label}</span>
      <div className="h-2.5 flex-1 overflow-hidden rounded bg-ops-panel-raised">
        <div className="h-full rounded" style={{ width: `${Math.max(value * 100, 2)}%`, background: color }} />
      </div>
      <span className="w-10 shrink-0 text-right font-mono text-ops-text">{(value * 100).toFixed(0)}%</span>
    </div>
  );
}

function ConfusionMatrix({ matrix }: { matrix: number[][] }) {
  // [[TN, FP], [FN, TP]]
  const [[tn, fp], [fn, tp]] = matrix;
  const total = tn + fp + fn + tp;
  const cell = (value: number, label: string, correct: boolean) => (
    <div
      className={`flex flex-col items-center justify-center rounded border p-4 ${
        correct ? "border-sev-low/40 bg-sev-low-bg" : "border-sev-high/40 bg-sev-high-bg"
      }`}
    >
      <span className={`font-mono text-2xl font-semibold ${correct ? "text-sev-low" : "text-sev-high"}`}>{value}</span>
      <span className="mt-1 text-center text-[10px] uppercase tracking-wide text-ops-text-dim">{label}</span>
      <span className="text-[10px] text-ops-text-faint">{total ? ((value / total) * 100).toFixed(1) : "0"}%</span>
    </div>
  );

  return (
    <div>
      <div className="grid grid-cols-[auto_1fr_1fr] gap-1.5 text-[10px]">
        <div />
        <div className="text-center text-ops-text-faint">Predicted NO-GO</div>
        <div className="text-center text-ops-text-faint">Predicted GO</div>

        <div className="flex items-center justify-center text-ops-text-faint [writing-mode:vertical-rl]">Actual NO-GO</div>
        {cell(tn, "True Negative", true)}
        {cell(fp, "False Positive", false)}

        <div className="flex items-center justify-center text-ops-text-faint [writing-mode:vertical-rl]">Actual GO</div>
        {cell(fn, "False Negative", false)}
        {cell(tp, "True Positive", true)}
      </div>
    </div>
  );
}

function ModelCard({ model }: { model: ModelMetrics }) {
  return (
    <div
      className={`rounded-lg border p-4 ${
        model.is_deployed ? "border-ops-accent-dim bg-ops-accent/5" : "border-ops-border bg-ops-panel/60"
      }`}
    >
      <div className="flex items-center justify-between">
        <h3 className="font-mono text-sm font-semibold text-ops-text">{model.display_name}</h3>
        {model.is_deployed && (
          <span className="rounded-full border border-ops-accent-dim bg-ops-accent/15 px-2 py-0.5 text-[10px] uppercase tracking-wide text-ops-accent">
            Deployed
          </span>
        )}
      </div>
      <p className="mt-1 text-[11px] text-ops-text-faint">Accuracy {(model.accuracy * 100).toFixed(1)}%</p>

      <div className="mt-3 space-y-2">
        <p className="text-[10px] uppercase tracking-wide text-ops-text-faint">NO-GO (the class that matters)</p>
        <MetricBar label="Precision" value={model.no_go.precision} color="#ef4444" />
        <MetricBar label="Recall" value={model.no_go.recall} color="#ef4444" />
        <MetricBar label="F1" value={model.no_go.f1_score} color="#ef4444" />
      </div>
      <div className="mt-3 space-y-2">
        <p className="text-[10px] uppercase tracking-wide text-ops-text-faint">GO</p>
        <MetricBar label="Precision" value={model.go.precision} color="#22c55e" />
        <MetricBar label="Recall" value={model.go.recall} color="#22c55e" />
        <MetricBar label="F1" value={model.go.f1_score} color="#22c55e" />
      </div>
      <p className="mt-3 text-[11px] text-ops-text-dim">
        Macro F1: <span className="font-mono text-ops-text">{(model.macro_f1 * 100).toFixed(1)}%</span>
      </p>
    </div>
  );
}

export function ModelPerformancePage() {
  const [data, setData] = useState<ModelPerformanceResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .modelPerformance()
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load model performance"));
  }, []);

  if (error) {
    return (
      <div className="flex min-h-0 flex-1 items-center justify-center p-6">
        <p className="text-sm text-sev-high">{error}</p>
      </div>
    );
  }
  if (!data) {
    return (
      <div className="flex min-h-0 flex-1 items-center justify-center p-6">
        <p className="text-sm text-ops-text-faint">Loading model performance…</p>
      </div>
    );
  }

  const deployed = data.models.find((m) => m.key === data.deployed_model_key) ?? data.models[0];

  return (
    <div className="min-h-0 flex-1 space-y-6 overflow-y-auto p-4">
      <div>
        <h2 className="text-xs font-mono uppercase tracking-wide text-ops-text-dim">Model Performance</h2>
        <p className="mt-1 text-[11px] text-ops-text-faint">
          Launch-weather go/no-go classifier — trained and evaluated on real historical data. See{" "}
          <span className="text-ops-text-dim">backend/data/launch_weather/PROVENANCE.md</span> for full data
          provenance.
        </p>
      </div>

      {/* Dataset & split */}
      <div className="rounded-lg border border-ops-border bg-ops-panel/60 p-4">
        <h3 className="font-mono text-xs uppercase tracking-wide text-ops-text-dim">Dataset &amp; Split</h3>
        <p className="mt-2 text-[12px] leading-relaxed text-ops-text-dim">{data.dataset.split_method}</p>
        <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div>
            <div className="font-mono text-lg text-ops-text">{data.dataset.total_rows}</div>
            <div className="text-[10px] uppercase tracking-wide text-ops-text-faint">Total real rows</div>
          </div>
          <div>
            <div className="font-mono text-lg text-ops-text">
              {data.dataset.train_rows} <span className="text-ops-text-faint">rows</span>
            </div>
            <div className="text-[10px] uppercase tracking-wide text-ops-text-faint">
              Train · {data.dataset.train_date_start} → {data.dataset.train_date_end}
            </div>
            <div className="text-[10px] text-ops-text-faint">
              {data.dataset.train_go} GO / {data.dataset.train_no_go} NO-GO
            </div>
          </div>
          <div>
            <div className="font-mono text-lg text-ops-text">
              {data.dataset.test_rows} <span className="text-ops-text-faint">rows</span>
            </div>
            <div className="text-[10px] uppercase tracking-wide text-ops-text-faint">
              Test · {data.dataset.test_date_start} → {data.dataset.test_date_end}
            </div>
            <div className="text-[10px] text-ops-text-faint">
              {data.dataset.test_go} GO / {data.dataset.test_no_go} NO-GO
            </div>
          </div>
          <div>
            <div className="font-mono text-lg text-sev-medium">
              {((data.dataset.train_no_go + data.dataset.test_no_go) / data.dataset.total_rows * 100).toFixed(1)}%
            </div>
            <div className="text-[10px] uppercase tracking-wide text-ops-text-faint">Overall NO-GO rate</div>
          </div>
        </div>
      </div>

      {/* Imbalance note */}
      <div className="rounded-lg border border-sev-medium/30 bg-sev-medium-bg px-4 py-3">
        <p className="text-[10px] font-semibold uppercase tracking-wide text-sev-medium">Class imbalance</p>
        <p className="mt-1 text-[12px] leading-relaxed text-ops-text-dim">{data.imbalance_note}</p>
      </div>

      {/* Deployed model confusion matrix */}
      <div className="rounded-lg border border-ops-border bg-ops-panel/60 p-4">
        <div className="flex items-center justify-between">
          <h3 className="font-mono text-xs uppercase tracking-wide text-ops-text-dim">
            Confusion Matrix — {deployed.display_name} (deployed)
          </h3>
          <span className="text-[10px] text-ops-text-faint">{data.selection_rule}</span>
        </div>
        <div className="mt-4 max-w-md">
          <ConfusionMatrix matrix={deployed.confusion_matrix} />
        </div>
      </div>

      {/* Model comparison */}
      <div>
        <h3 className="mb-3 font-mono text-xs uppercase tracking-wide text-ops-text-dim">
          Model Comparison — same train/test split
        </h3>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
          {data.models.map((m) => (
            <ModelCard key={m.key} model={m} />
          ))}
        </div>
      </div>
    </div>
  );
}
