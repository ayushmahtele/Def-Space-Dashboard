import { useEffect, useRef, useState } from "react";
import { MascotAvatar } from "./MascotAvatar";
import { TUTORIAL_STEPS } from "./steps";

const AVATAR_SIZE = 88;
const MARGIN = 12;

interface Anchor {
  left: number;
  top: number;
  usedFallback: boolean;
}

function computeAnchor(target: string): Anchor {
  const el = document.querySelector<HTMLElement>(`[data-tutorial="${target}"]`);
  if (!el) {
    return {
      left: window.innerWidth / 2 - AVATAR_SIZE / 2,
      top: window.innerHeight - AVATAR_SIZE - 140,
      usedFallback: true,
    };
  }
  const rect = el.getBoundingClientRect();
  const left = Math.min(
    Math.max(rect.right - AVATAR_SIZE - MARGIN, MARGIN),
    window.innerWidth - AVATAR_SIZE - MARGIN,
  );
  const top = Math.min(Math.max(rect.top + MARGIN, MARGIN), window.innerHeight - AVATAR_SIZE - 160);
  return { left, top, usedFallback: false };
}

interface TutorialOverlayProps {
  onDismiss: () => void;
}

// Guided walkthrough driven by the Mascot: moves (via CSS-transitioned position)
// to each dashboard section in turn and explains it. Skippable at any point;
// replays on every visit per project decision (no "seen it before" gating).
export function TutorialOverlay({ onDismiss }: TutorialOverlayProps) {
  const [stepIndex, setStepIndex] = useState(0);
  const [anchor, setAnchor] = useState<Anchor>(() => computeAnchor(TUTORIAL_STEPS[0].target));
  const [travelDirection, setTravelDirection] = useState(0);
  const prevLeftRef = useRef(anchor.left);

  const step = TUTORIAL_STEPS[stepIndex];

  useEffect(() => {
    const next = computeAnchor(step.target);
    setTravelDirection(Math.sign(next.left - prevLeftRef.current));
    prevLeftRef.current = next.left;
    setAnchor(next);

    const onResize = () => setAnchor(computeAnchor(step.target));
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, [step.target]);

  const isLast = stepIndex === TUTORIAL_STEPS.length - 1;
  const text = anchor.usedFallback && step.fallbackText ? step.fallbackText : step.text;

  return (
      <div className="pointer-events-none fixed inset-0 z-[2000]">
      <div
        className="pointer-events-auto absolute transition-all duration-700 ease-out"
        style={{ left: anchor.left, top: anchor.top, width: AVATAR_SIZE, height: AVATAR_SIZE }}
      >
        <MascotAvatar size={AVATAR_SIZE} travelDirection={travelDirection} />
      </div>

      <div
        className="pointer-events-auto absolute w-72 max-w-[calc(100vw-2rem)] rounded-lg border border-ops-border-strong bg-ops-panel-raised p-3 shadow-xl transition-all duration-700 ease-out"
        style={{
          left: Math.min(anchor.left, window.innerWidth - 288 - MARGIN),
          top: Math.min(anchor.top + AVATAR_SIZE + 8, window.innerHeight - 160),
        }}
      >
        <p className="text-xs leading-relaxed text-ops-text">{text}</p>
        <div className="mt-3 flex items-center justify-between">
          <button
            onClick={onDismiss}
            className="text-[11px] text-ops-text-dim underline decoration-dotted hover:text-ops-text"
          >
            Skip tutorial
          </button>
          <div className="flex items-center gap-2">
            {stepIndex > 0 && (
              <button
                onClick={() => setStepIndex((i) => i - 1)}
                className="rounded border border-ops-border px-2 py-1 text-[11px] text-ops-text-dim hover:text-ops-text"
              >
                Back
              </button>
            )}
            <button
              onClick={() => (isLast ? onDismiss() : setStepIndex((i) => i + 1))}
              className="rounded border border-ops-accent-dim bg-ops-accent/10 px-2 py-1 text-[11px] text-ops-accent hover:bg-ops-accent/20"
            >
              {isLast ? "Done" : "Next"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
