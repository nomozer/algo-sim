// Component harness (NOT the product page): Scene3DExplorer with scene = response.envelope.scene3d and
// routeD = response.route_d, both taken verbatim from the Adapter /2 fixture. Exposes the canonical
// response SHA-256 so the capture can compare it with manifest.json.
import React from "react";
import { createRoot } from "react-dom/client";
import { Scene3DExplorer } from "../src/simulations/domains/geometry/Scene3DExplorer";
import h07 from "../../docs/evaluation/geometry/runs/hybrid-preview-contract-hardening/fixtures-adapter-2/served-H07_PROOF_GOAL_NOT_PREMISE_BUT_CHECKED.json";
import h01 from "../../docs/evaluation/geometry/runs/hybrid-preview-contract-hardening/fixtures-adapter-2/served-H01_CUBE.json";
import "../src/styles/global.css";

const FX: Record<string, any> = { "served-H07_PROOF_GOAL_NOT_PREMISE_BUT_CHECKED": h07, "served-H01_CUBE": h01 };
const fx = FX[new URLSearchParams(location.search).get("id") ?? ""];
const canon = (v: any): string => v === null || typeof v !== "object" ? JSON.stringify(v)
  : Array.isArray(v) ? `[${v.map(canon).join(",")}]`
  : `{${Object.keys(v).sort().map((k) => `${JSON.stringify(k)}:${canon(v[k])}`).join(",")}}`;
crypto.subtle.digest("SHA-256", new TextEncoder().encode(canon(fx.response))).then((b) => {
  (window as any).__fixtureSha = [...new Uint8Array(b)].map((x) => x.toString(16).padStart(2, "0")).join("");
});
createRoot(document.getElementById("root")!).render(
  <div style={{ height: "100vh" }}>
    <Scene3DExplorer scene={fx.response.envelope.scene3d} routeD={fx.response.route_d} tieuDe={`HARNESS · ${fx.id}`} />
  </div>,
);
