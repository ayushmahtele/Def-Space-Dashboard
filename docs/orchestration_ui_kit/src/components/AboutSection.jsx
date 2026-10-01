/*
  AboutSection — the "AI Orchestration Engine / About" layout you liked:
  an eyebrow label, a large display heading, a lead paragraph, and a
  responsive grid of feature cards, all in the dark glass aesthetic.

  Everything is placeholder + generic — relabel `eyebrow`, `title`,
  `lead`, and the `features` array for your own project.
*/

const DEFAULT_FEATURES = [
  {
    icon: 'grid',
    title: 'Orchestration Engine',
    body: 'A central coordinator dispatches work to specialized agents and fuses their outputs into a single result.',
  },
  {
    icon: 'nodes',
    title: 'Agent Graph',
    body: 'Each agent is an independent node with a clear input and output, wired together into a visible pipeline.',
  },
  {
    icon: 'bolt',
    title: 'Real-time Flow',
    body: 'Data moves through the graph stage by stage, with every hand-off animated so the flow is legible at a glance.',
  },
  {
    icon: 'shield',
    title: 'Grounded Outputs',
    body: 'Results are traceable back to the stage that produced them — no black-box, every number has a source.',
  },
];

const ICONS = {
  grid: 'M3 3h7v7H3zM14 3h7v7h-7zM14 14h7v7h-7zM3 14h7v7H3z',
  nodes: 'M5 5a2 2 0 100 4 2 2 0 000-4zM19 5a2 2 0 100 4 2 2 0 000-4zM12 15a2 2 0 100 4 2 2 0 000-4zM7 7l4 8M17 7l-4 8',
  bolt: 'M13 2L3 14h7l-1 8 10-12h-7z',
  shield: 'M12 3l8 3v5c0 5-3.5 8-8 10-4.5-2-8-5-8-10V6z',
};

function FeatureCard({ icon, title, body }) {
  return (
    <div
      className="uikit-card"
      style={{ transition: 'border-color .35s, transform .35s, background .35s' }}
      onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'var(--border-glow)'; e.currentTarget.style.transform = 'translateY(-3px)'; }}
      onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'var(--border-mid)'; e.currentTarget.style.transform = 'translateY(0)'; }}
    >
      <span
        style={{
          width: 40, height: 40, borderRadius: 10,
          background: 'var(--tint-purple)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          marginBottom: 12,
        }}
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent-purple)" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
          <path d={ICONS[icon] || ICONS.grid} />
        </svg>
      </span>
      <h3 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)', margin: '0 0 6px' }}>{title}</h3>
      <p style={{ fontSize: 13, lineHeight: 1.6, color: 'var(--text-secondary)', margin: 0 }}>{body}</p>
    </div>
  );
}

export default function AboutSection({
  eyebrow = 'About the system',
  title = 'AI Orchestration Engine',
  lead = 'A coordinated set of specialized agents that each handle one job, then hand their results to a central engine that fuses them into a single, explainable output.',
  features = DEFAULT_FEATURES,
}) {
  return (
    <section style={{ maxWidth: 1080, margin: '0 auto', padding: '48px 24px' }}>
      <div style={{ maxWidth: 640, marginBottom: 40 }}>
        <span
          style={{
            fontSize: 11, letterSpacing: 3, textTransform: 'uppercase',
            color: 'var(--accent-purple)', fontWeight: 600,
          }}
        >
          {eyebrow}
        </span>
        <h2
          style={{
            fontSize: 'clamp(28px, 5vw, 44px)', fontWeight: 700, lineHeight: 1.1,
            color: 'var(--text-primary)', margin: '12px 0 16px',
            letterSpacing: '-0.02em',
          }}
        >
          {title}
        </h2>
        <p style={{ fontSize: 16, lineHeight: 1.7, color: 'var(--text-secondary)', margin: 0 }}>
          {lead}
        </p>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: 14,
        }}
      >
        {features.map((f, i) => (
          <FeatureCard key={i} {...f} />
        ))}
      </div>
    </section>
  );
}
