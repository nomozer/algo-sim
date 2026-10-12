// Scene3D HARNESS (not the product page) for scenes produced by the REAL Hybrid route — run `hybrid-slice-review`.
// Scenes: backend/scripts/export_hybrid_section_scenes.py → docs/.../hybrid-slice-review/visual/scenes.json.
// Renders with the product component `Scene3DWorkspace`; no store, no API, no model call.
// URL: ?i=<case index>&step=<formation step, default last>&aux=1. Exposes the product step model for the browser check.
import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import { Scene3DWorkspace } from "../src/simulations/domains/geometry/scene3d-view";
import { TRANG_THAI_DAU } from "../src/simulations/domains/geometry/interaction-state";
import { objectsAt, stepCount } from "../src/simulations/domains/geometry/scene3d-model";
import rows from "../../docs/evaluation/geometry/runs/hybrid-slice-review/visual/scenes.json";
import "../src/styles/global.css";

const q = new URLSearchParams(location.search);
const index = Number(q.get("i") ?? 0);
const row = (rows as any[])[index];
// Diagnostic only: `hide=<id>` drops one object, so a frame diff shows exactly the pixels that object contributes.
const hide = new Set((q.get("hide") ?? "").split(",").filter(Boolean));
// Diagnostic only: `set=<id>.<field>=<json>` overrides one field of one object (e.g. a line direction).
const sets = q.getAll("set").map((s) => { const [k, v] = s.split("="); const [id, f] = k.split("."); return { id, f, v: JSON.parse(v) }; });
const scene = { ...row.scene, objects: row.scene.objects.filter((o: any) => !hide.has(o.id))
  .map((o: any) => sets.filter((s) => s.id === o.id).reduce((a: any, s) => ({ ...a, [s.f]: s.v }), o)) } as any;
const n = stepCount(scene);
const step = q.has("step") ? Number(q.get("step")) : n - 1;
(window as any).__hybrid = {
  id: row.id, stepCount: n, step,
  presentAt: (k: number) => objectsAt(scene, k).map((o: any) => o.id),
  objects: scene.objects.map((o: any) => ({ id: o.id, type: o.type, origin: o.origin, depends: o.depends ?? [] })),
};

function Harness() {
  const [fit, setFit] = useState(0);
  return <main style={{ padding: 16, height: "100vh" }}>
    <h1>Scene3D harness / Hybrid IR / {row.id} / bước {step + 1}/{n}</h1>
    <button onClick={() => setFit(x => x + 1)}>Đặt lại khung nhìn</button>
    <div data-testid="khung" style={{ height: "75vh", minHeight: 440 }}>
      <Scene3DWorkspace scene={scene} step={step} interaction={TRANG_THAI_DAU} onSelect={() => undefined}
        fitToken={fit} auxiliaryShown={q.get("aux") === "1"} />
    </div>
  </main>;
}
createRoot(document.getElementById("root")!).render(<Harness />);
