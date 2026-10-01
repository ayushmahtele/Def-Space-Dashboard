import type { CSSProperties } from "react";

/*
  Ported from docs/orchestration_ui_kit/src/components/AboutSection.jsx into TypeScript.
  Logic/layout unchanged from the original — typed, and the ICONS map extended with a
  couple of extra glyphs (eye, globe, radio) per the kit README's own suggestion ("add
  more in the ICONS map") to cover our real agent list without every card falling back
  to the same icon.
*/

export interface Feature {
  icon: string;
  title: string;
  body: string;
}

const ICONS: Record<string, string> = {
  grid: "M3 3h7v7H3zM14 3h7v7h-7zM14 14h7v7h-7zM3 14h7v7H3z",
  nodes: "M5 5a2 2 0 100 4 2 2 0 000-4zM19 5a2 2 0 100 4 2 2 0 000-4zM12 15a2 2 0 100 4 2 2 0 000-4zM7 7l4 8M17 7l-4 8",
  bolt: "M13 2L3 14h7l-1 8 10-12h-7z",
  shield: "M12 3l8 3v5c0 5-3.5 8-8 10-4.5-2-8-5-8-10V6z",
  eye: "M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z M12 15a3 3 0 100-6 3 3 0 000 6z",
  globe: "M12 2a10 10 0 100 20 10 10 0 000-20z M2 12h20 M12 2c2.5 2.7 4 6.2 4 10s-1.5 7.3-4 10c-2.5-2.7-4-6.2-4-10s1.5-7.3 4-10z",
  radio: "M4 12a8 8 0 0116 0 M7 12a5 5 0 0110 0 M12 12a1 1 0 100 2 1 1 0 000-2z M12 15v6",
  target: "M12 2v4 M12 18v4 M2 12h4 M18 12h4 M12 8a4 4 0 100 8 4 4 0 000-8z",
};

function FeatureCard({ icon, title, body }: Feature) {
  return (
    <div
      className="uikit-card"
      style={{ transition: "border-color .35s, transform .35s, background .35s" }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = "var(--border-glow)";
        e.currentTarget.style.transform = "translateY(-3px)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = "var(--border-mid)";
        e.currentTarget.style.transform = "translateY(0)";
      }}
    >
      <span
        style={{
          width: 40,
          height: 40,
          borderRadius: 10,
          background: "var(--tint-purple)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          marginBottom: 12,
        }}
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent-purple)" strokeWidth={1.7} strokeLinecap="round" strokeLinejoin="round">
          <path d={ICONS[icon] || ICONS.grid} />
        </svg>
      </span>
      <h3 style={{ fontSize: 16, fontWeight: 600, color: "var(--text-primary)", margin: "0 0 6px" }}>{title}</h3>
      <p style={{ fontSize: 13, lineHeight: 1.6, color: "var(--text-secondary)", margin: 0 }}>{body}</p>
    </div>
  );
}

interface AboutSectionProps {
  eyebrow?: string;
  title?: string;
  lead?: string;
  features?: Feature[];
  style?: CSSProperties;
}

export default function AboutSection({
  eyebrow = "About the system",
  title = "AI Orchestration Engine",
  lead = "A coordinated set of specialized agents that each handle one job, then hand their results to a central engine that fuses them into a single, explainable output.",
  features = [],
  style,
}: AboutSectionProps) {
  return (
    <section style={{ maxWidth: 1080, margin: "0 auto", padding: "48px 24px", ...style }}>
      <div style={{ maxWidth: 640, marginBottom: 40 }}>
        <span
          style={{
            fontSize: 11,
            letterSpacing: 3,
            textTransform: "uppercase",
            color: "var(--accent-purple)",
            fontWeight: 600,
          }}
        >
          {eyebrow}
        </span>
        <h2
          style={{
            fontSize: "clamp(28px, 5vw, 44px)",
            fontWeight: 700,
            lineHeight: 1.1,
            color: "var(--text-primary)",
            margin: "12px 0 16px",
            letterSpacing: "-0.02em",
          }}
        >
          {title}
        </h2>
        <p style={{ fontSize: 16, lineHeight: 1.7, color: "var(--text-secondary)", margin: 0 }}>{lead}</p>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
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
