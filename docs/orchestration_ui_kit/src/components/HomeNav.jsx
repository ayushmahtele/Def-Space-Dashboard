/*
  HomeNav — the top-left "back to home" nav you liked.
  Fixed to the top-left corner, glassmorphism pill, with a logo mark,
  product name, and an optional back arrow.

  Usage:
    <HomeNav name="Your Project" tagline="SUBTITLE" onHome={() => navigate('/')} />

  Relabel `name` / `tagline` and swap the logo glyph for your own.
*/

export default function HomeNav({
  name = 'Your Project',
  tagline = 'PLATFORM',
  onHome = () => {},
}) {
  return (
    <button
      onClick={onHome}
      className="uikit-glass"
      style={{
        position: 'fixed',
        top: 18,
        left: 18,
        zIndex: 50,
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: '8px 14px 8px 10px',
        cursor: 'pointer',
        transition: 'border-color .3s, transform .3s',
      }}
      onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'var(--border-glow)'; e.currentTarget.style.transform = 'translateY(-1px)'; }}
      onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'var(--border-soft)'; e.currentTarget.style.transform = 'translateY(0)'; }}
    >
      {/* Logo mark — swap this glyph for your own icon/logo */}
      <span
        style={{
          width: 34,
          height: 34,
          borderRadius: 10,
          background: 'var(--grad-accent)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M3 12h4l2 5 4-12 2 7h6" />
        </svg>
      </span>

      <span style={{ textAlign: 'left', lineHeight: 1.15 }}>
        <span style={{ display: 'block', fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>{name}</span>
        <span style={{ display: 'block', fontSize: 9, letterSpacing: 2, color: 'var(--text-muted)', textTransform: 'uppercase' }}>{tagline}</span>
      </span>
    </button>
  );
}
