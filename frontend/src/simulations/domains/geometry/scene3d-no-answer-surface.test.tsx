import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { GEOMETRY_SAMPLES } from "../../../data/geometry-samples";
import { AxoWorkspaceV62 } from "../../../components/SimulationWorkspace";
import { buildPedagogicalConstructionPlan } from "./scene3d-semantic-policy";
import { evaluateStudentPresentationPolicy } from "./scene3d-student-presentation-policy";
import type { Scene3D } from "./scene3d-model";

/**
 * Quyết định sản phẩm 2026-11-05: luồng dựng hình KHÔNG có cơ chế trình bày đáp án — không nút
 * "Xem kết quả", không bảng "KẾT LUẬN", không nội dung ẩn chờ mở. Chứng nhận toán học (`goalCompletion`)
 * vẫn giữ để kiểm chứng.
 */
const sceneOf = (id: string) =>
  (GEOMETRY_SAMPLES.find(s => s.id === id)!.envelope as unknown as { scene3d: Scene3D }).scene3d;
const descOf = (id: string) => GEOMETRY_SAMPLES.find(s => s.id === id)!.envelope.description ?? "";
const ANSWER_SURFACE = ['id="dock-goal-reveal"', 'id="dock-goal-conclusion"', "data-conclusion-id", "KẾT LUẬN", "Xem kết quả", "Thu gọn kết quả"];

describe("Scene3D construction flow carries no answer presentation", () => {
  it("keeps the verified goal certificates (math data is not removed with the UI)", () => {
    for (const [id, values] of [["cau-the-tich", ["3", "36π"]], ["cau-cat-mat-phang", ["4", "16π"]]] as const) {
      const g = buildPedagogicalConstructionPlan(sceneOf(id)).goalCompletion;
      expect(g.status).toBe("reached");
      expect(g.items.map(i => i.valueText)).toEqual([...values]);
      expect(g.items.every(i => i.provenance === "DERIVED_VERIFIED")).toBe(true);
    }
  });

  it.each(GEOMETRY_SAMPLES.map(s => s.id))("%s: no reveal button, conclusion panel or hidden answer at any step", id => {
    const scene = sceneOf(id);
    const plan = buildPedagogicalConstructionPlan(scene);
    const answers = plan.goalCompletion.items
      .filter(i => i.provenance === "DERIVED_VERIFIED" && i.valueText && /[π√/]/u.test(i.valueText))
      .map(i => i.valueText!)
      .filter(v => !descOf(id).includes(v));
    const anchors = [0, Math.floor((plan.steps.length - 1) / 2), plan.steps.length - 1].map(i => plan.steps[i]!.anchor);
    for (const anchor of [...new Set(anchors)]) {
      const html = renderToString(<AxoWorkspaceV62 scene={scene} initialStep={anchor} de={descOf(id)} />);
      for (const marker of ANSWER_SURFACE) expect(html, `${id}@${anchor} ${marker}`).not.toContain(marker);
      for (const v of answers) expect(html, `${id}@${anchor} answer ${v}`).not.toContain(v);
    }
  });

  it("keeps given data and construction narration visible", () => {
    const html = renderToString(<AxoWorkspaceV62 scene={sceneOf("cau-cat-mat-phang")} initialStep={9999} de={descOf("cau-cat-mat-phang")} />);
    expect(html).toContain('id="dock-given-params"');
    expect(html).toContain("R = 5");
    expect(html).toContain("d(I, (P)) = 3");
    expect(html).toContain("Dựng đường tròn thiết diện");
  });

  it("construction-only problems get no closing calculation step", () => {
    for (const s of GEOMETRY_SAMPLES) {
      const plan = buildPedagogicalConstructionPlan(sceneOf(s.id));
      if (plan.goalCompletion.primaryKind !== "construction") continue;
      for (const step of plan.steps) {
        expect(step.epistemicCategory, `${s.id} ${step.title}`).not.toBe("conclusion");
        expect(step.stepRole, `${s.id} ${step.title}`).not.toBe("conclude_and_calculate");
      }
    }
  });

  it("policy and workspace source hold no answer-presentation state", () => {
    const policy = evaluateStudentPresentationPolicy(sceneOf("cau-the-tich"), buildPedagogicalConstructionPlan(sceneOf("cau-the-tich")).goalCompletion);
    expect(Object.keys(policy).sort()).toEqual([
      "canDisplayEntityFormula", "canDisplayEntityValue", "canRenderGeometricObject", "formatStudentObjectRole",
      "safeWorkspaceTitle", "showDiagnosticNotice", "showMathResultsPanel",
    ]);
    const root = join(__dirname, "../../..");
    const workspace = readFileSync(join(root, "components/SimulationWorkspace.tsx"), "utf8");
    const policySrc = readFileSync(join(__dirname, "scene3d-student-presentation-policy.ts"), "utf8");
    for (const src of [workspace, policySrc]) {
      for (const token of ["finalConclusions", "dock-goal-conclusion", "dock-goal-reveal", "Xem kết quả"]) expect(src).not.toContain(token);
    }
  });

  it("product code never mounts the legacy Scene3DExplorer (it has its own math-analysis panel)", () => {
    const root = join(__dirname, "../../..");
    for (const file of ["App.tsx", "components/SimulationWorkspace.tsx", "simulations/index.ts", "simulations/domains/semantic/index.ts"]) {
      expect(readFileSync(join(root, file), "utf8"), file).not.toMatch(/from\s+["'][^"']*Scene3DExplorer["']/u);
    }
  });
});
