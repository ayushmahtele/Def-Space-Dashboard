import { useEffect, useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { sampleTextPoints } from "./textParticles";

interface ParticleWordmarkProps {
  text: string;
  fontSize?: number;
  // Seconds from mount until particles are fully assembled into the wordmark.
  assembleDuration?: number;
  scale?: number;
  color?: string;
}

const PARTICLE_COUNT = 2400;
const SCATTER_RADIUS = 6;

function easeOutCubic(t: number) {
  return 1 - Math.pow(1 - t, 3);
}

export function ParticleWordmark({ text, fontSize, assembleDuration = 1.6, scale = 8, color = "#22d3ee" }: ParticleWordmarkProps) {
  const pointsRef = useRef<THREE.Points>(null);
  const groupRef = useRef<THREE.Group>(null);

  const { targets, starts } = useMemo(() => {
    const samples = sampleTextPoints(text, PARTICLE_COUNT, { fontSize });
    const targets = new Float32Array(PARTICLE_COUNT * 3);
    const starts = new Float32Array(PARTICLE_COUNT * 3);
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      const p = samples[i % samples.length] ?? { x: 0, y: 0 };
      targets[i * 3] = p.x * scale;
      targets[i * 3 + 1] = p.y * scale;
      targets[i * 3 + 2] = (Math.random() - 0.5) * 0.4;

      const theta = Math.random() * Math.PI * 2;
      const r = SCATTER_RADIUS * (0.4 + Math.random() * 0.8);
      starts[i * 3] = Math.cos(theta) * r;
      starts[i * 3 + 1] = Math.sin(theta) * r * 0.6;
      starts[i * 3 + 2] = (Math.random() - 0.5) * SCATTER_RADIUS;
    }
    return { targets, starts };
  }, [text, fontSize, scale]);

  const positions = useMemo(() => new Float32Array(targets.length), [targets]);

  const geometry = useMemo(() => {
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    return geo;
  }, [positions]);

  useFrame((state) => {
    const raw = THREE.MathUtils.clamp(state.clock.elapsedTime / assembleDuration, 0, 1);
    const t = easeOutCubic(raw);
    const posAttr = geometry.getAttribute("position") as THREE.BufferAttribute;
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      const ix = i * 3;
      posAttr.array[ix] = THREE.MathUtils.lerp(starts[ix], targets[ix], t);
      posAttr.array[ix + 1] = THREE.MathUtils.lerp(starts[ix + 1], targets[ix + 1], t);
      posAttr.array[ix + 2] = THREE.MathUtils.lerp(starts[ix + 2], targets[ix + 2], t);
    }
    posAttr.needsUpdate = true;

    if (groupRef.current) {
      groupRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.3) * 0.08 * (1 - t * 0.7);
    }
  });

  useEffect(() => {
    return () => geometry.dispose();
  }, [geometry]);

  return (
    <group ref={groupRef}>
      <points ref={pointsRef} geometry={geometry}>
        <pointsMaterial
          color={color}
          size={0.045}
          sizeAttenuation
          transparent
          opacity={0.9}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
        />
      </points>
    </group>
  );
}
