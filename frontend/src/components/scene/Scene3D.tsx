import { Canvas } from "@react-three/fiber";
import { Stars } from "@react-three/drei";
import { ParticleWordmark } from "../intro/ParticleWordmark";

interface Scene3DProps {
  text?: string;
  className?: string;
}

// Shared decorative 3D scene for Home and About: the same particle-assembly wordmark
// technique used by the loading screen (frontend/src/components/intro/ParticleWordmark.tsx),
// re-used here as persistent page decor rather than a one-shot intro — it assembles once
// on mount then idles with a gentle rotation wobble indefinitely.
export function Scene3D({ text = "DEF-SPACE", className = "h-56" }: Scene3DProps) {
  return (
    <div className={`relative w-full overflow-hidden ${className}`} style={{ background: "var(--grad-hero)" }}>
      <Canvas camera={{ position: [0, 0, 10], fov: 40 }}>
        <Stars radius={50} depth={30} count={1200} factor={2} saturation={0} fade speed={0.4} />
        <ParticleWordmark text={text} fontSize={150} scale={9.5} assembleDuration={1.8} />
      </Canvas>
    </div>
  );
}
