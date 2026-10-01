import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "leaflet/dist/leaflet.css";
import "./index.css";
import App from "./App.tsx";
import { IntroSequence } from "./components/intro/IntroSequence.tsx";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <IntroSequence>
      <App />
    </IntroSequence>
  </StrictMode>,
);
