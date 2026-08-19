import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import { registerAllSimulations } from "./simulations";
import { useAppStore } from "./state/store";
import "./styles/global.css";

registerAllSimulations();

if (typeof window !== "undefined") {
  (window as any).__ALGO_SIM_STORE__ = useAppStore;
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
