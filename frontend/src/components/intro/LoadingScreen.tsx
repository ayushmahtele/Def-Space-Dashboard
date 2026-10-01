import { useEffect } from "react";
import { Canvas } from "@react-three/fiber";
import { ParticleWordmark } from "./ParticleWordmark";

interface LoadingScreenProps {
  onComplete: () => void;
  // Total time this screen stays mounted before handing off, in ms.
  durationMs?: number;
}

// Plays once on first load: particles assemble into a BSERC wordmark placeholder.
// Swap ParticleWordmark for an actual logo texture once the real BSERC logo asset
// is dropped into the project (see docs/BUILD_SPEC.md).
export function LoadingScreen({ onComplete, durationMs = 2600 }: LoadingScreenProps) {
  useEffect(() => {
    const timer = setTimeout(onComplete, durationMs);
    return () => clearTimeout(timer);
  }, [onComplete, durationMs]);

  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-ops-bg">
      <div className="h-[220px] w-full max-w-3xl">
        <Canvas camera={{ position: [0, 0, 10], fov: 40 }}>
          <ParticleWordmark text="BSERC" assembleDuration={1.6} />
        </Canvas>
      </div>
      <p className="mt-2 text-xs tracking-[0.3em] text-ops-text-dim">
        SPACE EDUCATION RESEARCH CENTRE
      </p>
    </div>
  );
}
