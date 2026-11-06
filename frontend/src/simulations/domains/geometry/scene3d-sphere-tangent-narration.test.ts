import { describe, expect, it } from "vitest";
import type { Scene3D, SceneObject } from "./scene3d-model";
import { withSubEntities } from "./scene3d-subentities";
import { buildPedagogicalConstructionPlan, buildPedagogicalStepNarration } from "./scene3d-semantic-policy";

// d(K, (α)) = |3·0 + 4·25/4| / 5 = 5 = R ⇒ (α) tiếp xúc mặt cầu tại H = (3, 0, 4); KHÔNG có đường tròn giao tuyến.
const tangentScene: Scene3D = {
  free_objects: ["O_sph", "q_rad"],
  chart_metric: [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
  objects: [
    { id: "O_sph", type: "point3", label: "Tâm K", notation: "K", origin: "free", producer: null, render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
    { id: "q_rad", type: "quantity", label: "Bán kính mặt cầu", notation: "R", origin: "free", producer: null, render: "readout", depends: ["ball_k"], value: "5", exact: { kind: "rational", value: "5" }, source: { fact_id: "f_r", provenance: "GIVEN", is_given: true } as unknown as SceneObject["source"] },
    { id: "ball_k", type: "curved_solid", curved_kind: "ball", label: "Mặt cầu (S)", notation: "(S)", origin: "derived", producer: null, render: "curved_solid", depends: ["O_sph", "q_rad"], anchor: ["0", "0", "0"], radius_sq: "25" },
    { id: "mp_tan", type: "plane3", label: "Mặt phẳng tiếp diện (α)", notation: "(α)", origin: "derived", producer: null, render: "surface", surface_role: "CUTTING_PLANE", depends: [], point: ["0", "0", "25/4"], normal: ["3", "0", "4"] },
  ],
  events: [
    { step_index: 0, action: "INIT", object: null, depends: [], explanation: "" },
    { step_index: 1, action: "CREATE", object: "ball_k", depends: ["O_sph", "q_rad"], explanation: "" },
    { step_index: 2, action: "CREATE", object: "mp_tan", depends: [], explanation: "" },
  ],
};

describe("tangent plane (d = R) narration", () => {
  const plan = buildPedagogicalConstructionPlan(withSubEntities(tangentScene));
  const texts = plan.steps.map(step => {
    const n = buildPedagogicalStepNarration(plan.scene, step);
    return [step.title, step.subtitle, n.actionTitle, n.conciseRationale].filter(Boolean).join(" | ");
  });

  it("never claims an intersection circle", () => {
    for (const t of texts) expect(t).not.toMatch(/đường tròn giao tuyến/u);
  });

  it("foot step, then radius step that names H as the point of tangency without re-deriving it", () => {
    // Bước chân vuông góc riêng rồi mới tới bán kính KH (khoá §6 ở axo-sphere-and-cross-family-pedagogical-gate).
    const footSteps = texts.filter(t => /\bH\b/u.test(t));
    expect(footSteps).toHaveLength(2);
    expect(footSteps[1]).toMatch(/tiếp điểm/u);
    expect(footSteps[1]).not.toMatch(/hình chiếu vuông góc H/u);
  });
});
