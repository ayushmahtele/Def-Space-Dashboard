export interface TutorialStep {
  // Matches a `data-tutorial="<target>"` attribute on the element to point at.
  target: string;
  text: string;
  // Shown instead of `text` if the target element isn't in the DOM yet
  // (e.g. the predict result section before any query has run).
  fallbackText?: string;
}

export const TUTORIAL_STEPS: TutorialStep[] = [
  {
    target: "map",
    text: "Select any city whose AOI you want to know — click anywhere on the map to drop a point of interest.",
  },
  {
    target: "watchlist",
    text: "Your AOI watchlist lives here — saved regions, quick switching, and the details for whichever one is active.",
  },
  {
    target: "sitrep",
    text: "Run a query and the fused SITREP — your summary — shows up here, every claim tagged to the agent that produced it.",
  },
  {
    target: "predict",
    text: "The go/no-go model's verdict and its reasoning appear in this section.",
    fallbackText: "Once you run a query, the go/no-go model's verdict will appear here, with the reasoning behind it.",
  },
];
