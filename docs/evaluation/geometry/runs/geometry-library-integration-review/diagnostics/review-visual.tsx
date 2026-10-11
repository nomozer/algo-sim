// TEMPORARY reviewer harness (untracked, deleted after review). URL: ?i=<scene>&step=<n>&aux=1&sel=<id>
import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import { Scene3DWorkspace } from "../src/simulations/domains/geometry/scene3d-view";
import { TRANG_THAI_DAU } from "../src/simulations/domains/geometry/interaction-state";
import rows from "./review-scenes.json";
import "../src/styles/global.css";

const q = new URLSearchParams(location.search);

function Harness() {
  const index = Number(q.get("i") ?? 0);
  const step = Number(q.get("step") ?? 9999);
  const [selected, setSelected] = useState<string | null>(q.get("sel"));
  const row = (rows as any[])[index];
  (window as any).__review = { id: row.id, events: row.scene.events?.length ?? 0, objects: row.scene.objects.length };
  return <main style={{ padding: 8, height: "100vh" }}>
    <h1 style={{ fontSize: 14, margin: 0 }}>REVIEW / fake-provider / {row.id} / step {step} / sel {selected ?? "-"}</h1>
    <div style={{ height: "88vh", minHeight: 400 }}>
      <Scene3DWorkspace scene={row.scene} step={step} interaction={{ ...TRANG_THAI_DAU, selected_id: selected }}
        onSelect={setSelected} auxiliaryShown={q.get("aux") === "1"} />
    </div>
  </main>;
}
createRoot(document.getElementById("root")!).render(<Harness />);
