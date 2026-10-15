// Scene3D HARNESS (not the product page) for scenes produced by the REAL Hybrid route — runs `hybrid-slice-review`,
// `hybrid-semantic-hardening`. Scenes: backend/scripts/export_hybrid_section_scenes.py →
// docs/.../hybrid-semantic-hardening/visual/scenes.json.
// Renders with the product component `Scene3DWorkspace` AFTER the product's frame step `veKhongGian` (as
// `Scene3DExplorer` does; the `hybrid-slice-review` harness skipped it and drew payload coordinates). `frame=payload`
// keeps the old behaviour for comparison. No store, no API, no model call.
// URL: ?i=<case index>&step=<formation step, default last>&aux=1. Exposes the product step model for the browser check.
import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import { Scene3DWorkspace } from "../src/simulations/domains/geometry/scene3d-view";
import { TRANG_THAI_DAU, select } from "../src/simulations/domains/geometry/interaction-state";
import { geometryTimeline, objectsAt, stepCount, toVec3 } from "../src/simulations/domains/geometry/scene3d-model";
import { veKhongGian } from "../src/simulations/domains/geometry/scene3d-chart";
import rowsHardening from "../../docs/evaluation/geometry/runs/hybrid-semantic-hardening/visual/scenes.json";
import rowsGoal from "../../docs/evaluation/geometry/runs/goal-directed-section-planning/visual/scenes.json";
import rowsTwoLine from "../../docs/evaluation/geometry/runs/two-line-plane-section/visual/scenes.json";
import rowsSequencing from "../../docs/evaluation/geometry/runs/pedagogical-construction-sequencing/visual/scenes.json";
import rowsResultBinding from "../../docs/evaluation/geometry/runs/source-bound-result-planning/visual/scenes.json";
import "../src/styles/global.css";

const q = new URLSearchParams(location.search);
const index = Number(q.get("i") ?? 0);
// `src=goal`: scenes of run goal-directed-section-planning; default stays the frozen hardening export.
// `src=sequencing`: the same two-line problems after the learner construction order (run `pedagogical-construction-sequencing`).
const row = ((q.get("src") === "result-binding" ? rowsResultBinding : q.get("src") === "sequencing" ? rowsSequencing : q.get("src") === "two-line" ? rowsTwoLine : q.get("src") === "goal" ? rowsGoal : rowsHardening) as any[])[index];
// Diagnostic only: `hide=<id>` drops one object, so a frame diff shows exactly the pixels that object contributes.
const hide = new Set((q.get("hide") ?? "").split(",").filter(Boolean));
// Diagnostic only: `set=<id>.<field>=<json>` overrides one field of one object (e.g. a line direction).
const sets = q.getAll("set").map((s) => { const [k, v] = s.split("="); const [id, f] = k.split("."); return { id, f, v: JSON.parse(v) }; });
const khung = row.scene && { ...row.scene, objects: row.scene.objects.filter((o: any) => !hide.has(o.id))
  .map((o: any) => sets.filter((s) => s.id === o.id).reduce((a: any, s) => ({ ...a, [s.f]: s.v }), o)) } as any;
const scene = khung && (q.get("frame") === "payload" ? khung : veKhongGian(khung));
const n = scene ? stepCount(scene) : 0;

function Harness() {
  const [fit, setFit] = useState(0);
  const [step, setStep] = useState(q.has("step") ? Number(q.get("step")) : n - 1);
  const [interaction, setInteraction] = useState(TRANG_THAI_DAU);
  (window as any).__hybrid = {
    id: row.id, served: row.served, stepCount: n, step, selected_id: interaction.selected_id,
    presentAt: (k: number) => scene ? objectsAt(scene, k).map((o: any) => o.id) : [],
    objects: scene ? scene.objects.map((o: any) => ({ id: o.id, type: o.type, origin: o.origin, depends: o.depends ?? [],
      label: o.label, role: o.role, source: o.source, endpoint_entities: o.endpoint_entities, render: o.render })) : [],
    // Learner steps of the product scrubber (`Scene3DExplorer` shows frame `anchor` of each) and the WORLD coordinates
    // the renderer receives after `veKhongGian` — for the playback audit (`hybrid-section-visual-check.mjs --playback`).
    timeline: scene ? geometryTimeline(scene).map(({ index, start, end, anchor }) => ({ index, start, end, anchor })) : [],
    world: scene ? Object.fromEntries(scene.objects.filter((o: any) => o.type === "point3").map((o: any) => [o.id, toVec3(o.xyz)])) : {},
  };
  if (!row.served || !scene) return <main style={{ padding: 16 }}>
    <h1>Scene3D harness / Hybrid IR / {row.id}</h1>
    <p data-testid="refusal">{row.code}: {row.reason ?? "Từ chối an toàn"}</p>
  </main>;
  return <main style={{ padding: 16, height: "100vh" }}>
    <h1>Scene3D harness / Hybrid IR / {row.id} / bước {step + 1}/{n}</h1>
    <div style={{ display: "flex", flexWrap: "wrap", gap: 16, alignItems: "center", marginBottom: 8 }}>
    <button onClick={() => setFit(x => x + 1)}>Đặt lại khung nhìn</button>
    <label>Bước dựng <input aria-label="Bước dựng" type="range" min={0} max={n - 1} value={step}
      onChange={e => setStep(Number(e.target.value))} /></label>
    <label>Chọn đối tượng <select aria-label="Chọn đối tượng" value={interaction.selected_id ?? ""}
      onChange={e => setInteraction(s => select(s, e.target.value || null))}>
      <option value="">Bỏ chọn</option>
      {objectsAt(scene, step).filter((o: any) => o.render !== "non_visual").map((o: any) =>
        <option key={o.id} value={o.id}>{o.label || o.id}{o.source?.binding === "AUXILIARY" ? ` · ${o.role}` : ""}</option>)}
    </select></label>
    </div>
    {interaction.selected_id && <p data-testid="selection-details">{scene.objects.filter((o: any) =>
      o.id === interaction.selected_id).map((o: any) => `${o.label} · ${o.role}`).join("")}</p>}
    <div data-testid="khung" style={{ height: "75vh", minHeight: 440 }}>
      <Scene3DWorkspace scene={scene} step={step} interaction={{ ...interaction, current_step: step }}
        onSelect={id => setInteraction(s => select(s, id))}
        fitToken={fit} auxiliaryShown={q.get("aux") === "1"} />
    </div>
  </main>;
}
createRoot(document.getElementById("root")!).render(<Harness />);
