import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";

interface MascotProps {
  // -1..1, horizontal direction the mascot is currently traveling; tilts the body that way.
  travelDirection?: number;
  color?: string;
}

// Small original probe-bot mascot (not modeled on any existing character): a rounded
// body, a single scanning "eye", a thin antenna, and two side thruster rings that glow
// while idling. Built entirely from primitive geometries — no external model asset.
export function Mascot({ travelDirection = 0, color = "#22d3ee" }: MascotProps) {
  const groupRef = useRef<THREE.Group>(null);
  const eyeRef = useRef<THREE.Mesh>(null);
  const leftThrusterRef = useRef<THREE.Mesh>(null);
  const rightThrusterRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    const t = state.clock.elapsedTime;
    if (groupRef.current) {
      groupRef.current.position.y = Math.sin(t * 1.8) * 0.08;
      groupRef.current.rotation.z = THREE.MathUtils.lerp(groupRef.current.rotation.z, travelDirection * -0.25, 0.08);
      groupRef.current.rotation.y = Math.sin(t * 0.6) * 0.15;
    }
    if (eyeRef.current) {
      const blink = Math.max(0, Math.sin(t * 0.5)) > 0.97 ? 0.1 : 1;
      eyeRef.current.scale.y = THREE.MathUtils.lerp(eyeRef.current.scale.y, blink, 0.5);
    }
    const pulse = 0.6 + Math.sin(t * 4) * 0.3;
    if (leftThrusterRef.current) {
      (leftThrusterRef.current.material as THREE.MeshStandardMaterial).emissiveIntensity = pulse;
    }
    if (rightThrusterRef.current) {
      (rightThrusterRef.current.material as THREE.MeshStandardMaterial).emissiveIntensity = pulse;
    }
  });

  return (
    <group ref={groupRef}>
      <ambientLight intensity={0.5} />
      <pointLight position={[2, 2, 3]} intensity={1.2} color={color} />

      {/* body */}
      <mesh>
        <capsuleGeometry args={[0.5, 0.35, 8, 16]} />
        <meshStandardMaterial color="#161d29" metalness={0.6} roughness={0.35} />
      </mesh>

      {/* eye / scanner lens */}
      <mesh ref={eyeRef} position={[0, 0.05, 0.48]}>
        <sphereGeometry args={[0.16, 16, 16]} />
        <meshStandardMaterial color={color} emissive={color} emissiveIntensity={1.2} />
      </mesh>

      {/* antenna */}
      <mesh position={[0, 0.85, 0]}>
        <cylinderGeometry args={[0.015, 0.015, 0.4, 6]} />
        <meshStandardMaterial color="#4c5a6c" />
      </mesh>
      <mesh position={[0, 1.06, 0]}>
        <sphereGeometry args={[0.05, 8, 8]} />
        <meshStandardMaterial color={color} emissive={color} emissiveIntensity={1} />
      </mesh>

      {/* side thrusters */}
      <mesh ref={leftThrusterRef} position={[-0.55, -0.2, 0]}>
        <torusGeometry args={[0.14, 0.04, 8, 16]} />
        <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.6} />
      </mesh>
      <mesh ref={rightThrusterRef} position={[0.55, -0.2, 0]}>
        <torusGeometry args={[0.14, 0.04, 8, 16]} />
        <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.6} />
      </mesh>
    </group>
  );
}
