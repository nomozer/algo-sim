import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import { registerAllSimulations } from "./simulations";
import "./styles/global.css";

registerAllSimulations();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
