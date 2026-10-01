/*
  DemoApp — shows every kit component together so you can see the full
  look-and-feel. Use this as a reference, then copy the individual
  components you want into your real project.

  Setup in your project:
    1. import './styles/theme.css'   (once, in main.jsx)
    2. wrap your app root in <div className="uikit-app">
    3. drop in any component below
*/

import HomeNav from './components/HomeNav';
import AboutSection from './components/AboutSection';
import OrchestrationEngine from './components/OrchestrationEngine';
import AgentGraph from './components/AgentGraph';
import './styles/theme.css';

export default function DemoApp() {
  return (
    <div className="uikit-app">
      <HomeNav name="Your Project" tagline="PLATFORM" onHome={() => alert('go home')} />

      {/* Hero-ish intro */}
      <section style={{ maxWidth: 1080, margin: '0 auto', padding: '90px 24px 20px', textAlign: 'center' }}>
        <span className="uikit-chip" style={{ marginBottom: 16 }}>
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--accent-green)' }} />
          5 agents active
        </span>
        <h1 style={{ fontSize: 'clamp(32px, 6vw, 56px)', fontWeight: 700, letterSpacing: '-0.03em', lineHeight: 1.05, margin: '16px 0', color: 'var(--text-primary)' }}>
          AI Orchestration Engine
        </h1>
        <p style={{ maxWidth: 560, margin: '0 auto', fontSize: 17, lineHeight: 1.6, color: 'var(--text-secondary)' }}>
          A generic, relabelable UI kit — dark glass aesthetic, 3D pipeline animation, and agent graph. Swap the labels, keep the look.
        </p>
      </section>

      {/* The centerpiece 3D animation */}
      <section style={{ maxWidth: 900, margin: '0 auto', padding: '20px 24px' }}>
        <OrchestrationEngine tilt={34} />
      </section>

      {/* Static graph */}
      <section style={{ maxWidth: 720, margin: '0 auto', padding: '20px 24px' }}>
        <h2 style={{ fontSize: 13, letterSpacing: 2, textTransform: 'uppercase', color: 'var(--accent-purple)', marginBottom: 14 }}>Agent orchestration graph</h2>
        <AgentGraph />
      </section>

      {/* About */}
      <AboutSection />

      <footer style={{ textAlign: 'center', padding: '40px 24px', color: 'var(--text-faint)', fontSize: 12 }}>
        Generic UI kit · relabel everything · same look, your content
      </footer>
    </div>
  );
}
