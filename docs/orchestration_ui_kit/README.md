# Orchestration UI Kit

A generic, relabelable version of the dark-glass agent-orchestration interface — the 3D animated pipeline, the agent graph, the top-left home nav, the About-section layout, and the full design-token system. Built for **React + Vite + Tailwind** (works without Tailwind too — all styles are plain CSS + inline styles, no Tailwind classes required).

## What's included

| File | What it is |
|---|---|
| `src/styles/theme.css` | The design system — all colors, spacing, radius, type, glows as CSS variables. **Edit this to re-skin everything at once.** |
| `src/components/HomeNav.jsx` | Fixed top-left "back to home" glass pill with logo + name. |
| `src/components/AboutSection.jsx` | Eyebrow + big heading + lead + feature-card grid. |
| `src/components/OrchestrationEngine.jsx` | The centerpiece — deep-3D animated pipeline. Fully configurable via props. |
| `src/components/AgentGraph.jsx` | Clean static node-link diagram of orchestrator → agents → output. |
| `src/DemoApp.jsx` | Shows everything together. Reference only. |

## Setup (3 steps)

1. Copy the `src/components/` files and `src/styles/theme.css` into your project.
2. Import the theme once, e.g. in your `main.jsx`:
   ```js
   import './styles/theme.css';
   ```
3. Wrap your app root (or any page) so it inherits the base atmosphere:
   ```jsx
   <div className="uikit-app">
     {/* your pages */}
   </div>
   ```

## Relabeling (this is the point — keep the look, change the content)

### HomeNav
```jsx
<HomeNav name="My New App" tagline="DASHBOARD" onHome={() => navigate('/')} />
```
Swap the inline `<svg>` logo glyph inside `HomeNav.jsx` for your own.

### AboutSection
```jsx
<AboutSection
  eyebrow="About"
  title="My Engine"
  lead="One-sentence description."
  features={[
    { icon: 'grid',   title: 'Feature one', body: '...' },
    { icon: 'nodes',  title: 'Feature two', body: '...' },
  ]}
/>
```
Available icons: `grid`, `nodes`, `bolt`, `shield` (add more in the `ICONS` map).

### OrchestrationEngine (the 3D animation)
The default shows a generic `data → process → agents → fuse → output` pipeline.
To make it yours, pass three props:

```jsx
<OrchestrationEngine
  tilt={34}                 // 3D angle in degrees — lower = flatter/more readable, higher = more dramatic
  layers={myLayers}         // rows of nodes, front-to-back
  edges={myEdges}           // [fromId, toId] connections
  script={mySteps}          // timed animation steps
  verdictFields={myFields}  // optional bottom result cards
  headerLabel="My pipeline · live"
/>
```

- **layers**: array of rows. Each node = `{ id, label, sub, outs? }`. `outs` is an optional list of output-line element IDs shown inside the node.
- **edges**: `[['orch','src1'], ['src1','proc'], ...]`.
- **script**: array of `{ at, active?, done?, packets?, out?, log?, tilt?, verdict? }` steps (see `DEFAULT_SCRIPT` in the file for the exact shape). `at` is milliseconds.
- **verdictFields**: `[{ label:'Result', value:'BUY', id:'v-res', color:'#34d399' }]` — the `value` shows when a step has `verdict:true`.

**Changing the tilt anytime**: just change the `tilt` number. The camera-lean-in near the end auto-adjusts to it.

### AgentGraph (static diagram)
```jsx
<AgentGraph
  nodes={[
    { id:'orch', label:'Head', x:0.5, y:0.15, accent:'#a78bfa', big:true },
    { id:'a1',   label:'Worker A', x:0.25, y:0.55, accent:'#60a5fa' },
    ...
  ]}
  links={[['orch','a1'], ...]}
/>
```
`x`/`y` are 0..1 relative positions, so the layout scales with its container.

## Re-skinning the whole kit

Every component reads from `theme.css` variables. To change the entire palette, edit the `--accent-*`, `--surface-*`, and `--bg-*` values in one place. For example, to move from purple to teal, change `--accent-purple` and `--border-glow` and the whole kit follows.

## Notes

- All icons are inline SVG — no icon library dependency required.
- Animation respects `prefers-reduced-motion`.
- The 3D uses CSS `perspective` + `transform`, not WebGL — light, and won't conflict with a separate Three.js scene elsewhere in your app.
- No backend wiring included — these are pure presentation components. Feed them your own data via props.
