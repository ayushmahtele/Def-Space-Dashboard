import { useEffect, useRef, useCallback } from "react";

/*
  Ported from docs/orchestration_ui_kit/src/components/OrchestrationEngine.jsx into
  TypeScript so it type-checks under this project's strict tsconfig (no allowJs).
  Logic is unchanged from the original — only typed. See that file's header comment
  and docs/orchestration_ui_kit/README.md for how the props work.

  No default layers/edges/script are kept here on purpose: this component is only ever
  meant to render our real pipeline (see frontend/src/components/workflow/pipeline.ts),
  never the kit's generic placeholder content, so layers/edges/script are required props.
*/

export interface EngineNode {
  id: string;
  label: string;
  sub: string;
  outs?: string[];
}

export type EngineLayer = EngineNode[];
export type EngineEdge = [string, string];

export interface ScriptStep {
  at: number;
  active?: string[];
  done?: string[];
  packets?: [string, string, string][];
  out?: [string, string];
  log?: [string, string];
  tilt?: boolean;
  verdict?: boolean;
}

export interface VerdictField {
  label: string;
  value: string;
  id: string;
  color?: string;
}

interface OrchestrationEngineProps {
  tilt?: number;
  layers: EngineLayer[];
  edges: EngineEdge[];
  script: ScriptStep[];
  verdictFields?: VerdictField[] | null;
  headerLabel?: string;
}

const Z = [0, -120, -240, -360, -480, -600];
const Y = [10, 90, 190, 285, 385, 480];

export default function OrchestrationEngine({
  tilt = 34,
  layers,
  edges,
  script,
  verdictFields = null,
  headerLabel = "Orchestration engine",
}: OrchestrationEngineProps) {
  const boardRef = useRef<HTMLDivElement>(null);
  const nodesRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const logRef = useRef<HTMLDivElement>(null);
  const starsRef = useRef<HTMLCanvasElement>(null);
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([]);
  const pathsRef = useRef<Record<string, SVGPathElement>>({});

  const drawWires = useCallback(() => {
    const board = boardRef.current,
      svg = svgRef.current;
    if (!board || !svg) return;
    svg.innerHTML = "";
    const b = board.getBoundingClientRect();
    const center = (id: string) => {
      const el = document.getElementById("oe-nd-" + id);
      if (!el) return { x: 0, y: 0 };
      const r = el.getBoundingClientRect();
      return { x: (r.left + r.right) / 2 - b.left, y: (r.top + r.bottom) / 2 - b.top };
    };
    edges.forEach(([a, cc]) => {
      const p1 = center(a),
        p2 = center(cc),
        my = (p1.y + p2.y) / 2;
      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      path.setAttribute("d", `M ${p1.x} ${p1.y} C ${p1.x} ${my}, ${p2.x} ${my}, ${p2.x} ${p2.y}`);
      path.setAttribute("fill", "none");
      path.setAttribute("stroke", "rgba(139,92,246,0.14)");
      path.setAttribute("stroke-width", "1.3");
      svg.appendChild(path);
      pathsRef.current[a + ">" + cc] = path;
    });
  }, [edges]);

  const packet = useCallback((a: string, b: string, color: string) => {
    const path = pathsRef.current[a + ">" + b];
    const svg = svgRef.current;
    if (!path || !svg) return;
    path.setAttribute("stroke", "rgba(139,92,246,0.55)");
    path.setAttribute("stroke-width", "2");
    const dot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    dot.setAttribute("r", "4");
    dot.setAttribute("fill", color);
    dot.style.filter = `drop-shadow(0 0 5px ${color})`;
    svg.appendChild(dot);
    const len = path.getTotalLength();
    const t0 = performance.now();
    const dur = 750;
    function step(t: number) {
      const k = Math.min((t - t0) / dur, 1);
      const p = path!.getPointAtLength(len * k);
      dot.setAttribute("cx", String(p.x));
      dot.setAttribute("cy", String(p.y));
      if (k < 1) requestAnimationFrame(step);
      else {
        dot.remove();
        path!.setAttribute("stroke", "rgba(139,92,246,0.14)");
        path!.setAttribute("stroke-width", "1.3");
      }
    }
    requestAnimationFrame(step);
  }, []);

  const run = useCallback(() => {
    const $ = (id: string) => document.getElementById(id);
    const st = (id: string, s: "active" | "done" | null) => {
      const n = $("oe-nd-" + id);
      if (!n) return;
      n.classList.remove("oe-active", "oe-done");
      if (s) n.classList.add(s === "active" ? "oe-active" : "oe-done");
      const e = $("oe-s-" + id);
      if (e) e.textContent = s === "active" ? "run" : s === "done" ? "ok" : "idle";
    };
    const out = (id: string, v: string) => {
      const el = $(id);
      if (el) el.innerHTML = v;
    };
    const addLog = (t: string, c: string) => {
      const log = logRef.current;
      if (!log) return;
      const d = document.createElement("div");
      d.style.color = c || "rgba(255,255,255,0.6)";
      d.innerHTML = t;
      log.prepend(d);
      while (log.children.length > 5) log.lastChild!.remove();
    };
    const board = boardRef.current;

    timersRef.current.forEach(clearTimeout);
    timersRef.current = [];
    layers.flat().forEach((n) => st(n.id, null));
    layers.flat().forEach((n) => (n.outs || []).forEach((o) => out(o, "—")));
    if (board) board.style.transform = `rotateX(${tilt}deg) scale(0.92)`;
    setTimeout(drawWires, 60);

    script.forEach((step) => {
      timersRef.current.push(
        setTimeout(() => {
          (step.active || []).forEach((id) => st(id, "active"));
          (step.done || []).forEach((id) => st(id, "done"));
          (step.packets || []).forEach(([a, b, c]) => packet(a, b, c));
          if (step.out) out(step.out[0], step.out[1]);
          if (step.log) addLog(step.log[0], step.log[1]);
          if (step.tilt && board) board.style.transform = `rotateX(${Math.max(tilt - 14, 8)}deg) scale(0.98)`;
          if (step.verdict && verdictFields) {
            verdictFields.forEach((f) => {
              const el = $(f.id);
              if (el) el.textContent = f.value;
            });
          }
        }, step.at),
      );
    });
  }, [drawWires, packet, tilt, layers, script, verdictFields]);

  useEffect(() => {
    const wrap = nodesRef.current;
    if (!wrap) return;
    wrap.innerHTML = "";
    layers.forEach((layer, li) => {
      const row = document.createElement("div");
      row.className = "oe-layer";
      row.style.top = Y[li] + "px";
      row.style.transform = "translateZ(" + Z[li] + "px)";
      layer.forEach((n) => {
        const el = document.createElement("div");
        el.className = "oe-node";
        el.id = "oe-nd-" + n.id;
        let outs = "";
        if (n.outs) outs = n.outs.map((o) => `<div class="oe-out" id="${o}">—</div>`).join("");
        el.innerHTML =
          `<div class="oe-nh"><span class="oe-dot"></span><span>${n.label}</span><em id="oe-s-${n.id}">idle</em></div>` +
          `<div class="oe-sub">${n.sub}</div>${outs}`;
        row.appendChild(el);
      });
      wrap.appendChild(row);
    });

    const cnv = starsRef.current;
    if (cnv) {
      const ctx = cnv.getContext("2d");
      cnv.width = cnv.offsetWidth;
      cnv.height = cnv.offsetHeight;
      if (ctx) {
        for (let i = 0; i < 80; i++) {
          ctx.globalAlpha = Math.random() * 0.5 + 0.1;
          ctx.fillStyle = "#fff";
          ctx.beginPath();
          ctx.arc(Math.random() * cnv.width, Math.random() * cnv.height, Math.random() * 1.2, 0, 7);
          ctx.fill();
        }
        ctx.globalAlpha = 1;
      }
    }

    const onResize = () => drawWires();
    window.addEventListener("resize", onResize);
    const t = setTimeout(run, 150);
    return () => {
      window.removeEventListener("resize", onResize);
      clearTimeout(t);
      timersRef.current.forEach(clearTimeout);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div style={{ background: "var(--bg-deep)", borderRadius: 12, overflow: "hidden", position: "relative" }}>
      <style>{`
        .oe-layer{ position:absolute; left:0; right:0; display:flex; justify-content:center; gap:14px; transform-style:preserve-3d; }
        .oe-node{ position:relative; background:var(--surface-1); border:1px solid var(--border-mid); border-radius:13px; padding:11px 13px; min-width:150px; transform-style:preserve-3d; transition:transform .5s cubic-bezier(.2,.8,.2,1), border-color .4s, box-shadow .5s, background .4s; backface-visibility:hidden; }
        .oe-node.oe-active{ border-color:var(--border-glow); background:rgba(50,40,90,0.9); box-shadow:var(--glow-purple), var(--shadow-lift); transform:translateZ(70px) scale(1.05); }
        .oe-node.oe-done{ border-color:rgba(52,211,153,0.5); background:rgba(20,40,34,0.8); }
        .oe-nh{ display:flex; align-items:center; gap:7px; font-size:12.5px; font-weight:500; color:var(--text-primary); }
        .oe-dot{ width:8px; height:8px; border-radius:50%; background:var(--accent-purple); flex-shrink:0; }
        .oe-node.oe-done .oe-dot{ background:var(--accent-green); }
        .oe-nh em{ margin-left:auto; font-style:normal; font-size:9px; padding:2px 6px; border-radius:99px; background:rgba(255,255,255,0.07); color:var(--text-muted); text-transform:uppercase; letter-spacing:.5px; }
        .oe-node.oe-active .oe-nh em{ background:rgba(139,92,246,0.3); color:#ddd6fe; }
        .oe-node.oe-done .oe-nh em{ background:rgba(52,211,153,0.18); color:#6ee7b7; }
        .oe-sub{ font-size:10px; color:var(--text-muted); margin-top:4px; line-height:1.4; }
        .oe-out{ font-size:10.5px; color:var(--text-secondary); margin-top:4px; font-family:var(--font-mono); }
        .oe-out b{ color:var(--accent-cyan); font-weight:500; }
      `}</style>

      <div style={{ position: "absolute", inset: 0, background: "var(--grad-hero)", pointerEvents: "none" }} />
      <canvas
        ref={starsRef}
        style={{ position: "absolute", inset: 0, width: "100%", height: "100%", pointerEvents: "none", opacity: 0.6 }}
      />

      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "14px 16px 8px",
          position: "relative",
          zIndex: 10,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span
            style={{
              width: 8,
              height: 8,
              borderRadius: "50%",
              background: "var(--accent-green)",
              boxShadow: "var(--glow-soft)",
            }}
          />
          <span style={{ fontSize: 11, color: "var(--text-secondary)", letterSpacing: 2, textTransform: "uppercase" }}>
            {headerLabel}
          </span>
        </div>
        <button
          onClick={run}
          style={{
            fontSize: 12,
            color: "var(--accent-purple)",
            background: "var(--tint-purple)",
            border: "0.5px solid var(--border-glow)",
            borderRadius: 8,
            padding: "5px 13px",
            cursor: "pointer",
          }}
        >
          Replay run
        </button>
      </div>

      <div style={{ perspective: "1100px", perspectiveOrigin: "50% 30%", height: 560, position: "relative", zIndex: 2 }}>
        <div
          ref={boardRef}
          style={{
            position: "absolute",
            inset: 0,
            transformStyle: "preserve-3d",
            transform: `rotateX(${tilt}deg) scale(0.92)`,
            transition: "transform 1s",
          }}
        >
          <svg
            ref={svgRef}
            style={{ position: "absolute", left: 0, top: 0, width: "100%", height: "100%", overflow: "visible", transformStyle: "preserve-3d" }}
          />
          <div ref={nodesRef} />
        </div>
      </div>

      {verdictFields && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: `repeat(${verdictFields.length},1fr)`,
            gap: 8,
            margin: "0 14px 10px",
            position: "relative",
            zIndex: 10,
          }}
        >
          {verdictFields.map((f) => (
            <div
              key={f.id}
              style={{
                background: "var(--surface-2)",
                border: "0.5px solid var(--border-soft)",
                borderRadius: 10,
                padding: "7px 6px",
                textAlign: "center",
              }}
            >
              <div style={{ fontSize: 9, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: ".8px" }}>
                {f.label}
              </div>
              <div style={{ fontSize: 15, fontWeight: 500, color: f.color || "var(--text-primary)", marginTop: 2 }} id={f.id}>
                —
              </div>
            </div>
          ))}
        </div>
      )}

      <div
        style={{
          margin: "0 14px 14px",
          background: "rgba(0,0,0,0.55)",
          border: "0.5px solid var(--border-soft)",
          borderRadius: 10,
          padding: "9px 12px",
          height: 92,
          overflow: "hidden",
          position: "relative",
          zIndex: 10,
        }}
      >
        <div ref={logRef} style={{ fontFamily: "var(--font-mono)", fontSize: 11, lineHeight: 1.75 }} />
      </div>
    </div>
  );
}
