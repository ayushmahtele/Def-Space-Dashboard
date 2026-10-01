import { useEffect, useRef, useCallback } from 'react';

/*
  OrchestrationEngine — the deep-3D animated pipeline you liked, made fully
  generic and configurable. A central orchestrator dispatches to data sources,
  which feed processing stages, which feed worker agents, which fuse into a
  final result.

  ── HOW TO RELABEL ──
  Pass your own `layers` array. Each layer is a row of nodes (front to back).
  Each node: { id, label, sub, outs? }  (outs = optional output lines shown
  inside the node). Wire them with `edges` ([fromId, toId] pairs). Drive the
  animation with a `script` array of timed steps. Defaults below produce a
  generic "data -> process -> agents -> fuse -> output" pipeline.

  ── TILT ──
  <OrchestrationEngine tilt={34} />  // change degrees anytime
*/

const DEFAULT_LAYERS = [
  [{ id: 'orch', label: 'Orchestrator', sub: 'Coordinates all agents' }],
  [
    { id: 'src1', label: 'Data source 1', sub: 'primary feed' },
    { id: 'src2', label: 'Data source 2', sub: 'secondary feed' },
    { id: 'src3', label: 'Data source 3', sub: 'external feed' },
  ],
  [
    { id: 'proc', label: 'Processor', sub: 'transforms inputs' },
    { id: 'enrich', label: 'Enricher', sub: 'adds context' },
  ],
  [
    { id: 'agentA', label: 'Agent A', sub: 'model · variant 1', outs: ['a-out'] },
    { id: 'agentB', label: 'Agent B', sub: 'model · variant 2', outs: ['b-out'] },
  ],
  [
    { id: 'fuse', label: 'Fusion', sub: 'combines outputs', outs: ['f-out'] },
    { id: 'score', label: 'Scorer', sub: 'confidence', outs: ['s-out'] },
  ],
  [{ id: 'final', label: 'Output agent', sub: 'final result' }],
];

const DEFAULT_EDGES = [
  ['orch', 'src1'], ['orch', 'src2'], ['orch', 'src3'],
  ['src1', 'proc'], ['src3', 'enrich'], ['enrich', 'proc'],
  ['proc', 'agentA'], ['src2', 'agentB'],
  ['agentA', 'fuse'], ['agentB', 'fuse'],
  ['fuse', 'score'], ['fuse', 'final'],
];

// A step: { at (ms), active?, done?, packets?[[a,b,color]], out?[id,html], log?[text,color] }
const DEFAULT_SCRIPT = [
  { at: 300, active: ['orch'], log: ['[orch] cycle start · dispatching', '#c4b5fd'] },
  { at: 1000, packets: [['orch', 'src1', '#a78bfa'], ['orch', 'src2', '#a78bfa'], ['orch', 'src3', '#a78bfa']] },
  { at: 1700, done: ['orch'], active: ['src1', 'src2', 'src3'], log: ['[data] sources responding', '#38bdf8'] },
  { at: 2900, done: ['src1', 'src3'], packets: [['src1', 'proc', '#38bdf8'], ['src3', 'enrich', '#38bdf8']] },
  { at: 3500, active: ['enrich'], log: ['[enrich] adding context', '#f472b6'] },
  { at: 4600, done: ['enrich'], packets: [['enrich', 'proc', '#f472b6']] },
  { at: 5100, active: ['proc'], log: ['[proc] transforming inputs', '#a78bfa'] },
  { at: 6300, done: ['proc', 'src2'], packets: [['proc', 'agentA', '#7dd3fc'], ['src2', 'agentB', '#fbbf24']] },
  { at: 6900, active: ['agentA', 'agentB'], log: ['[agents] running models', '#60a5fa'] },
  { at: 8100, out: ['a-out', 'result → <b>value A</b>'] },
  { at: 9300, out: ['b-out', 'result → <b>value B</b>'], done: ['agentA', 'agentB'] },
  { at: 10200, packets: [['agentA', 'fuse', '#7dd3fc'], ['agentB', 'fuse', '#fbbf24']] },
  { at: 11000, active: ['fuse'], out: ['f-out', 'fused → <b>combined</b>'], log: ['[fusion] combining outputs', '#6ee7b7'], packets: [['fuse', 'score', '#34d399']] },
  { at: 12000, active: ['score'], out: ['s-out', 'confidence → <b>—</b>'], log: ['[score] scoring result', '#6ee7b7'] },
  { at: 12800, done: ['score', 'fuse'], packets: [['fuse', 'final', '#c084fc']] },
  { at: 13500, active: ['final'], log: ['[output] preparing final result', '#c084fc'], tilt: true },
  { at: 15000, done: ['final'], log: ['[orch] verdict published', '#6ee7b7'], verdict: true },
];

const Z = [0, -120, -240, -360, -480, -600];
const Y = [10, 90, 190, 285, 385, 480];

export default function OrchestrationEngine({
  tilt = 34,
  layers = DEFAULT_LAYERS,
  edges = DEFAULT_EDGES,
  script = DEFAULT_SCRIPT,
  verdictFields = null, // e.g. [{label:'Result', value:'—', id:'v-res', color:'#34d399'}]
  headerLabel = 'Orchestration engine · demo',
}) {
  const boardRef = useRef(null);
  const nodesRef = useRef(null);
  const svgRef = useRef(null);
  const logRef = useRef(null);
  const starsRef = useRef(null);
  const timersRef = useRef([]);
  const pathsRef = useRef({});

  const drawWires = useCallback(() => {
    const board = boardRef.current, svg = svgRef.current;
    if (!board || !svg) return;
    svg.innerHTML = '';
    const b = board.getBoundingClientRect();
    const center = (id) => {
      const el = document.getElementById('oe-nd-' + id);
      if (!el) return { x: 0, y: 0 };
      const r = el.getBoundingClientRect();
      return { x: (r.left + r.right) / 2 - b.left, y: (r.top + r.bottom) / 2 - b.top };
    };
    edges.forEach(([a, cc]) => {
      const p1 = center(a), p2 = center(cc), my = (p1.y + p2.y) / 2;
      const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      path.setAttribute('d', `M ${p1.x} ${p1.y} C ${p1.x} ${my}, ${p2.x} ${my}, ${p2.x} ${p2.y}`);
      path.setAttribute('fill', 'none');
      path.setAttribute('stroke', 'rgba(139,92,246,0.14)');
      path.setAttribute('stroke-width', '1.3');
      svg.appendChild(path);
      pathsRef.current[a + '>' + cc] = path;
    });
  }, [edges]);

  const packet = useCallback((a, b, color) => {
    const path = pathsRef.current[a + '>' + b];
    const svg = svgRef.current;
    if (!path || !svg) return;
    path.setAttribute('stroke', 'rgba(139,92,246,0.55)');
    path.setAttribute('stroke-width', '2');
    const dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    dot.setAttribute('r', '4');
    dot.setAttribute('fill', color);
    dot.style.filter = `drop-shadow(0 0 5px ${color})`;
    svg.appendChild(dot);
    const len = path.getTotalLength();
    const t0 = performance.now();
    const dur = 750;
    function step(t) {
      const k = Math.min((t - t0) / dur, 1);
      const p = path.getPointAtLength(len * k);
      dot.setAttribute('cx', p.x);
      dot.setAttribute('cy', p.y);
      if (k < 1) requestAnimationFrame(step);
      else {
        dot.remove();
        path.setAttribute('stroke', 'rgba(139,92,246,0.14)');
        path.setAttribute('stroke-width', '1.3');
      }
    }
    requestAnimationFrame(step);
  }, []);

  const run = useCallback(() => {
    const $ = (id) => document.getElementById(id);
    const st = (id, s) => {
      const n = $('oe-nd-' + id);
      if (!n) return;
      n.classList.remove('oe-active', 'oe-done');
      if (s) n.classList.add(s === 'active' ? 'oe-active' : 'oe-done');
      const e = $('oe-s-' + id);
      if (e) e.textContent = s === 'active' ? 'run' : s === 'done' ? 'ok' : 'idle';
    };
    const out = (id, v) => { const el = $(id); if (el) el.innerHTML = v; };
    const addLog = (t, c) => {
      const log = logRef.current; if (!log) return;
      const d = document.createElement('div');
      d.style.color = c || 'rgba(255,255,255,0.6)';
      d.innerHTML = t;
      log.prepend(d);
      while (log.children.length > 5) log.lastChild.remove();
    };
    const board = boardRef.current;

    timersRef.current.forEach(clearTimeout);
    timersRef.current = [];
    layers.flat().forEach((n) => st(n.id, null));
    layers.flat().forEach((n) => (n.outs || []).forEach((o) => out(o, '—')));
    if (board) board.style.transform = `rotateX(${tilt}deg) scale(0.92)`;
    setTimeout(drawWires, 60);

    script.forEach((step) => {
      timersRef.current.push(setTimeout(() => {
        (step.active || []).forEach((id) => st(id, 'active'));
        (step.done || []).forEach((id) => st(id, 'done'));
        (step.packets || []).forEach(([a, b, c]) => packet(a, b, c));
        if (step.out) out(step.out[0], step.out[1]);
        if (step.log) addLog(step.log[0], step.log[1]);
        if (step.tilt && board) board.style.transform = `rotateX(${Math.max(tilt - 14, 8)}deg) scale(0.98)`;
        if (step.verdict && verdictFields) {
          verdictFields.forEach((f) => { const el = $(f.id); if (el) el.textContent = f.value; });
        }
      }, step.at));
    });
  }, [drawWires, packet, tilt, layers, script, verdictFields]);

  useEffect(() => {
    const wrap = nodesRef.current;
    if (!wrap) return;
    wrap.innerHTML = '';
    layers.forEach((layer, li) => {
      const row = document.createElement('div');
      row.className = 'oe-layer';
      row.style.top = Y[li] + 'px';
      row.style.transform = 'translateZ(' + Z[li] + 'px)';
      layer.forEach((n) => {
        const el = document.createElement('div');
        el.className = 'oe-node';
        el.id = 'oe-nd-' + n.id;
        let outs = '';
        if (n.outs) outs = n.outs.map((o) => `<div class="oe-out" id="${o}">—</div>`).join('');
        el.innerHTML =
          `<div class="oe-nh"><span class="oe-dot"></span><span>${n.label}</span><em id="oe-s-${n.id}">idle</em></div>` +
          `<div class="oe-sub">${n.sub}</div>${outs}`;
        row.appendChild(el);
      });
      wrap.appendChild(row);
    });

    const cnv = starsRef.current;
    if (cnv) {
      const ctx = cnv.getContext('2d');
      cnv.width = cnv.offsetWidth; cnv.height = cnv.offsetHeight;
      for (let i = 0; i < 80; i++) {
        ctx.globalAlpha = Math.random() * 0.5 + 0.1;
        ctx.fillStyle = '#fff';
        ctx.beginPath();
        ctx.arc(Math.random() * cnv.width, Math.random() * cnv.height, Math.random() * 1.2, 0, 7);
        ctx.fill();
      }
      ctx.globalAlpha = 1;
    }

    const onResize = () => drawWires();
    window.addEventListener('resize', onResize);
    const t = setTimeout(run, 150);
    return () => { window.removeEventListener('resize', onResize); clearTimeout(t); timersRef.current.forEach(clearTimeout); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div style={{ background: 'var(--bg-deep)', borderRadius: 12, overflow: 'hidden', position: 'relative' }}>
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

      <div style={{ position: 'absolute', inset: 0, background: 'var(--grad-hero)', pointerEvents: 'none' }} />
      <canvas ref={starsRef} style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none', opacity: 0.6 }} />

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 16px 8px', position: 'relative', zIndex: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--accent-green)', boxShadow: 'var(--glow-soft)' }} />
          <span style={{ fontSize: 11, color: 'var(--text-secondary)', letterSpacing: 2, textTransform: 'uppercase' }}>{headerLabel}</span>
        </div>
        <button onClick={run} style={{ fontSize: 12, color: 'var(--accent-purple)', background: 'var(--tint-purple)', border: '0.5px solid var(--border-glow)', borderRadius: 8, padding: '5px 13px', cursor: 'pointer' }}>Replay run</button>
      </div>

      <div style={{ perspective: '1100px', perspectiveOrigin: '50% 30%', height: 560, position: 'relative', zIndex: 2 }}>
        <div ref={boardRef} style={{ position: 'absolute', inset: 0, transformStyle: 'preserve-3d', transform: `rotateX(${tilt}deg) scale(0.92)`, transition: 'transform 1s' }}>
          <svg ref={svgRef} style={{ position: 'absolute', left: 0, top: 0, width: '100%', height: '100%', overflow: 'visible', transformStyle: 'preserve-3d' }} />
          <div ref={nodesRef} />
        </div>
      </div>

      {verdictFields && (
        <div style={{ display: 'grid', gridTemplateColumns: `repeat(${verdictFields.length},1fr)`, gap: 8, margin: '0 14px 10px', position: 'relative', zIndex: 10 }}>
          {verdictFields.map((f) => (
            <div key={f.id} style={{ background: 'var(--surface-2)', border: '0.5px solid var(--border-soft)', borderRadius: 10, padding: '7px 6px', textAlign: 'center' }}>
              <div style={{ fontSize: 9, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '.8px' }}>{f.label}</div>
              <div style={{ fontSize: 15, fontWeight: 500, color: f.color || 'var(--text-primary)', marginTop: 2 }} id={f.id}>—</div>
            </div>
          ))}
        </div>
      )}

      <div style={{ margin: '0 14px 14px', background: 'rgba(0,0,0,0.55)', border: '0.5px solid var(--border-soft)', borderRadius: 10, padding: '9px 12px', height: 92, overflow: 'hidden', position: 'relative', zIndex: 10 }}>
        <div ref={logRef} style={{ fontFamily: 'var(--font-mono)', fontSize: 11, lineHeight: 1.75 }} />
      </div>
    </div>
  );
}
