import { useEffect, useRef } from 'react';

/*
  AgentGraph — a clean, static (non-animated) node-link diagram of an
  orchestrator coordinating agents. Good for an About page or a "how it
  works" panel where you want the structure shown at a glance without the
  full running animation.

  Relabel via `nodes` and `links`. Each node has a position (0..1 relative
  to the box) so it scales with the container.
*/

const DEFAULT_NODES = [
  { id: 'orch', label: 'Orchestrator', x: 0.5, y: 0.15, accent: '#a78bfa', big: true },
  { id: 'a1', label: 'Agent 1', x: 0.2, y: 0.5, accent: '#60a5fa' },
  { id: 'a2', label: 'Agent 2', x: 0.5, y: 0.5, accent: '#fbbf24' },
  { id: 'a3', label: 'Agent 3', x: 0.8, y: 0.5, accent: '#f472b6' },
  { id: 'out', label: 'Output', x: 0.5, y: 0.85, accent: '#34d399', big: true },
];

const DEFAULT_LINKS = [
  ['orch', 'a1'], ['orch', 'a2'], ['orch', 'a3'],
  ['a1', 'out'], ['a2', 'out'], ['a3', 'out'],
];

export default function AgentGraph({ nodes = DEFAULT_NODES, links = DEFAULT_LINKS, height = 340 }) {
  const boxRef = useRef(null);
  const svgRef = useRef(null);

  useEffect(() => {
    const box = boxRef.current, svg = svgRef.current;
    if (!box || !svg) return;
    const draw = () => {
      const w = box.clientWidth, h = box.clientHeight;
      svg.innerHTML = '';
      const pos = (id) => {
        const n = nodes.find((x) => x.id === id);
        return { x: n.x * w, y: n.y * h };
      };
      links.forEach(([a, b]) => {
        const p1 = pos(a), p2 = pos(b);
        const my = (p1.y + p2.y) / 2;
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', `M ${p1.x} ${p1.y} C ${p1.x} ${my}, ${p2.x} ${my}, ${p2.x} ${p2.y}`);
        path.setAttribute('fill', 'none');
        path.setAttribute('stroke', 'rgba(139,92,246,0.25)');
        path.setAttribute('stroke-width', '1.4');
        svg.appendChild(path);
      });
    };
    draw();
    window.addEventListener('resize', draw);
    return () => window.removeEventListener('resize', draw);
  }, [nodes, links]);

  return (
    <div
      ref={boxRef}
      style={{
        position: 'relative',
        height,
        background: 'var(--bg-deep)',
        border: '0.5px solid var(--border-soft)',
        borderRadius: 'var(--r-lg)',
        overflow: 'hidden',
      }}
    >
      <div style={{ position: 'absolute', inset: 0, background: 'var(--grad-hero)', pointerEvents: 'none' }} />
      <svg ref={svgRef} style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', overflow: 'visible' }} />
      {nodes.map((n) => (
        <div
          key={n.id}
          style={{
            position: 'absolute',
            left: `${n.x * 100}%`,
            top: `${n.y * 100}%`,
            transform: 'translate(-50%, -50%)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 6,
            zIndex: 2,
          }}
        >
          <div
            style={{
              width: n.big ? 60 : 46,
              height: n.big ? 60 : 46,
              borderRadius: '50%',
              background: 'var(--surface-1)',
              border: `1.5px solid ${n.accent}66`,
              boxShadow: `0 0 20px ${n.accent}33`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: n.accent }} />
          </div>
          <span style={{ fontSize: 11, color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>{n.label}</span>
        </div>
      ))}
    </div>
  );
}
