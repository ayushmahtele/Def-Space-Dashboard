import { useCallback, useRef, useState } from "react";
import { Canvas } from "@react-three/fiber";
import type { RootState } from "@react-three/fiber";
import { Mascot } from "./Mascot";

interface MascotAvatarProps {
  size?: number;
  travelDirection?: number;
}

const MAX_RECOVERY_ATTEMPTS = 3;
const RENDER_HEALTH_CHECK_MS = 700;

function canvasHasDrawnPixels(canvas: HTMLCanvasElement): boolean {
  const probe = document.createElement("canvas");
  probe.width = canvas.width;
  probe.height = canvas.height;
  const ctx = probe.getContext("2d");
  if (!ctx || canvas.width === 0 || canvas.height === 0) return false;
  ctx.drawImage(canvas, 0, 0);
  const { data } = ctx.getImageData(0, 0, probe.width, probe.height);
  for (let i = 3; i < data.length; i += 4) {
    if (data[i] > 0) return true;
  }
  return false;
}

// Small fixed-size Canvas rendering just the mascot, meant to be placed inside a
// CSS-positioned/animated wrapper (see TutorialOverlay) so "moving toward a feature"
// is a container-position transition while the 3D character itself keeps idling.
//
// Two failure modes are handled defensively, both of which leave a *correctly sized,
// correctly positioned* canvas element that simply shows nothing — indistinguishable
// from empty space rather than an obviously broken 3D scene:
//   1. An actual `webglcontextlost` event (GPU driver hiccup, too many concurrent
//      contexts) — remount with a fresh context, a few times, then give up.
//   2. A context that reports healthy (`isContextLost() === false`) but never actually
//      paints a pixel — seen on some constrained/virtualized GPU setups where WebGL
//      "works" per the API but the driver silently no-ops draw calls. There's no event
//      for this, so it's detected by sampling the canvas's own pixels shortly after
//      mount; if nothing was ever drawn, the canvas is hidden for good.
// Either way, a small glowing marker is always rendered underneath so the avatar never
// reads as truly empty — a lost-context canvas paints as opaque black rather than
// transparent, so it's hidden outright rather than relied on to let the marker show
// through.
export function MascotAvatar({ size = 96, travelDirection = 0 }: MascotAvatarProps) {
  const [canvasKey, setCanvasKey] = useState(0);
  const [hidden, setHidden] = useState(false);
  const [renderFailed, setRenderFailed] = useState(false);
  const attemptsRef = useRef(0);

  const handleCreated = useCallback(({ gl }: RootState) => {
    const canvas = gl.domElement;

    const onLost = (e: Event) => {
      e.preventDefault();
      setHidden(true);
      attemptsRef.current += 1;
      if (attemptsRef.current > MAX_RECOVERY_ATTEMPTS) {
        setRenderFailed(true);
        return;
      }
      setTimeout(() => {
        setCanvasKey((k) => k + 1);
        setHidden(false);
      }, 300);
    };
    canvas.addEventListener("webglcontextlost", onLost, { once: true });

    setTimeout(() => {
      if (!canvasHasDrawnPixels(canvas)) {
        setRenderFailed(true);
      }
    }, RENDER_HEALTH_CHECK_MS);
  }, []);

  return (
    <div style={{ width: size, height: size, position: "relative" }}>
      {/* CSS/SVG stand-in for the 3D mascot (rounded body, single glowing eye, antenna) —
          same design language as Mascot.tsx's geometry, so it reads as the same
          character rather than an unrelated placeholder. Always rendered; the 3D canvas
          layers on top when it's actually able to paint. */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <svg width={size * 0.62} height={size * 0.62} viewBox="0 0 40 40" style={{ animation: "mascot-bob 2.6s ease-in-out infinite" }}>
          <line x1="20" y1="4" x2="20" y2="10" stroke="#4c5a6c" strokeWidth="1.6" />
          <circle cx="20" cy="3" r="2" fill="#22d3ee">
            <animate attributeName="opacity" values="1;0.4;1" dur="1.8s" repeatCount="indefinite" />
          </circle>
          <rect x="8" y="10" width="24" height="24" rx="12" fill="#161d29" stroke="#34455c" strokeWidth="1" />
          <circle cx="20" cy="21" r="5" fill="#22d3ee">
            <animate attributeName="opacity" values="1;1;0.15;1;1" dur="4s" repeatCount="indefinite" />
          </circle>
        </svg>
        <style>{`@keyframes mascot-bob { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-3px); } }`}</style>
      </div>
      {!renderFailed && (
        <div style={{ width: "100%", height: "100%", visibility: hidden ? "hidden" : "visible" }}>
          <Canvas key={canvasKey} camera={{ position: [0, 0, 3], fov: 45 }} gl={{ alpha: true }} onCreated={handleCreated}>
            <Mascot travelDirection={travelDirection} />
          </Canvas>
        </div>
      )}
    </div>
  );
}
