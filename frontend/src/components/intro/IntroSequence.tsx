import { useState, type ReactNode } from "react";
import { LoadingScreen } from "./LoadingScreen";

type Phase = "loading" | "done";

// Plays the loading screen once, then reveals whatever content is passed as children.
// The separate welcome screen was retired in favor of the Home page (which now serves as
// the app's permanent front door, reachable anytime via nav) — see docs/SESSION_HANDOFF.md.
export function IntroSequence({ children }: { children: ReactNode }) {
  const [phase, setPhase] = useState<Phase>("loading");

  if (phase === "loading") {
    return <LoadingScreen onComplete={() => setPhase("done")} />;
  }
  return <>{children}</>;
}
