import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { UnsupportedNotice } from "../../../components/SimulationWorkspace";
import { Scene3DExplorer } from "./Scene3DExplorer";
import { annotationsAt, DEFAULT_ANNOTATION_VIEW } from "./scene3d-annotations";
import {
  geometryAnchor,
  geometryNarrationAt,
  geometryStepCount,
  geometryStepList,
  phanLoaiVat,
  phanTichToanHocCuaCanh,
  quantityChoices,
  stepCount,
  tapKetQuaCuoi,
  type RouteDSimulationSummary,
  type Scene3D,
} from "./scene3d-model";
import { withSubEntities } from "./scene3d-subentities";
import { taoTrangThai } from "./interaction-state";

interface AuditRow {
  id: string;
  family: string;
  category: string;
  served: boolean;
  problem_text?: string;
  scene?: Scene3D;
  route_d?: RouteDSimulationSummary;
  code?: string;
  reason?: string;
}

const AUDIT_SCENES: AuditRow[] = JSON.parse(
  readFileSync(
    fileURLToPath(
      new URL(
        "../../../../../docs/evaluation/geometry/runs/simulation-visual-consistency-learning-ux/demos/audit_scenes.json",
        import.meta.url,
      ),
    ),
    "utf8",
  ),
);

const SERVED_SCENES = AUDIT_SCENES.filter((r) => r.served && r.scene);

describe("Session 2 (P6–P10) — Simulation-First Learning Experience & Mathematical Analysis", () => {
  it("P6: Mode A (Simulation) is the default across all 13 served families; Mode B button is present and panel is closed by default", () => {
    expect(SERVED_SCENES.length).toBe(13);
    for (const row of SERVED_SCENES) {
      const scene = row.scene!;
      const before = JSON.stringify(scene);
      const html = renderToString(
        <Scene3DExplorer
          scene={scene}
          de={row.problem_text ?? row.category}
          tieuDe={row.category}
          routeDSimulation={row.route_d ?? null}
        />,
      );
      expect(html, `${row.id}: Mode B button should exist`).toContain('data-mo-bang="phan-tich"');
      expect(html, `${row.id}: Mode B button text`).toContain("Phân tích toán học");
      expect(html, `${row.id}: Mode B panel must be closed by default in Mode A`).not.toContain(
        "data-math-analysis-panel",
      );
      // Scene3D must never be mutated by rendering
      expect(JSON.stringify(scene)).toBe(before);
    }
  });

  it("P6 & P7: Mode A hides all requested final results from canvas annotations and quantity choices across all steps", () => {
    for (const row of SERVED_SCENES) {
      const day = withSubEntities(row.scene!);
      const ketQua = tapKetQuaCuoi(day, null);
      const n = stepCount(day);
      for (let k = 0; k < n; k += 1) {
        const annsDefault = annotationsAt(day, k, { ...DEFAULT_ANNOTATION_VIEW, hiddenIds: ketQua }, null);
        const visibleDefault = annsDefault.filter((a) => !ketQua.has(a.id));
        for (const a of visibleDefault) {
          expect(ketQua.has(a.id), `${row.id} step ${k} leaked ${a.id}`).toBe(false);
        }
        const q = quantityChoices(day, k);
        const modeAResults = q.results.filter((id) => !ketQua.has(id));
        const modeASteps = q.steps.filter((id) => !ketQua.has(id));
        expect(modeAResults, `${row.id} step ${k} results in Mode A`).toEqual([]);
        for (const id of modeASteps) {
          expect(ketQua.has(id)).toBe(false);
        }
      }
    }
  });

  it("P6: If a geometry scene has no mathematical results, measurements, or certificates, no analysis panel button is fabricated", () => {
    const pureScene: Scene3D = {
      objects: [
        {
          id: "A",
          label: "Điểm A",
          notation: "A",
          type: "point3",
          render: "point_marker",
          origin: "free",
          producer: null,
          depends: [],
          xyz: ["0", "0", "0"],
          parent: null,
          display_group: ["given"],
          source: {},
        },
        {
          id: "B",
          label: "Điểm B",
          notation: "B",
          type: "point3",
          render: "point_marker",
          origin: "free",
          producer: null,
          depends: [],
          xyz: ["2", "0", "0"],
          parent: null,
          display_group: ["given"],
          source: {},
        },
      ],
      events: [
        { step_index: 0, action: "INIT", object: null, depends: [], explanation: "Khởi tạo hai điểm A, B." },
      ],
      free_objects: ["A", "B"],
    };
    const pt = phanTichToanHocCuaCanh(pureScene);
    expect(pt.requestedResults).toEqual([]);
    expect(pt.derivedMeasurements).toEqual([]);
    expect(pt.givenDimensions).toEqual([]);
    expect(pt.certificates).toEqual([]);
    const html = renderToString(<Scene3DExplorer scene={pureScene} />);
    expect(html).not.toContain('data-mo-bang="phan-tich"');
  });

  it("P7: Semantic classification distinguishes GIVEN_DIMENSION, DERIVED_MEASUREMENT, REQUESTED_RESULT, GEOMETRY_IDENTITY, and MATHEMATICAL_CERTIFICATE structurally", () => {
    const coneRow = SERVED_SCENES.find((r) => r.id === "family10_cone_frustum_cut")!;
    const coneScene = withSubEntities(coneRow.scene!);
    const kq = tapKetQuaCuoi(coneScene);

    const rObj = coneScene.objects.find((o) => o.id === "R")!;
    const hObj = coneScene.objects.find((o) => o.id === "h")!;
    const volObj = coneScene.objects.find((o) => o.id === "kq_m_vol")!;
    const axialObj = coneScene.objects.find((o) => o.id === "td_sec_axial")!;
    const apexObj = coneScene.objects.find((o) => o.id === "S")!;

    expect(phanLoaiVat(coneScene, rObj, kq)).toBe("GIVEN_DIMENSION");
    expect(phanLoaiVat(coneScene, hObj, kq)).toBe("GIVEN_DIMENSION");
    expect(phanLoaiVat(coneScene, volObj, kq)).toBe("REQUESTED_RESULT");
    expect(phanLoaiVat(coneScene, axialObj, kq)).toBe("GEOMETRY_IDENTITY");
    expect(phanLoaiVat(coneScene, apexObj, kq)).toBe("GEOMETRY_IDENTITY");

    const ptCone = phanTichToanHocCuaCanh(coneScene, null, coneRow.route_d);
    expect(ptCone.givenDimensions.map((x) => `${x.notation}=${x.valueDisplay}`)).toEqual([
      "R=3",
      "h=4",
      "r=3/2",
    ]);
    const coneResultValues = ptCone.requestedResults.map((x) => x.valueDisplay);
    expect(coneResultValues).toContain("12π");
    expect(coneResultValues).toContain("15π");
    expect(coneResultValues).toContain("12");
    expect(coneResultValues).toContain("1/8");
    expect(coneResultValues).toContain("21π/2");
    expect(ptCone.certificates.some((c) => c.certificateRule === "cone_frustum_parallel_cut_complement")).toBe(true);

    // Check derived sub-pyramid (family04): vcert volumes are intermediate in Mode B while hidden in Mode A
    const subPyrRow = SERVED_SCENES.find((r) => r.id === "family04_derived_sub_pyramid")!;
    const subPyrScene = withSubEntities(subPyrRow.scene!);
    const subPyrKq = tapKetQuaCuoi(subPyrScene);
    expect(subPyrKq.has("kq_vcert10")).toBe(true);
    expect(subPyrKq.has("kq_vcert11")).toBe(true);
    const ptSubPyr = phanTichToanHocCuaCanh(subPyrScene, null, subPyrRow.route_d);
    expect(ptSubPyr.derivedMeasurements.map((d) => d.id)).toEqual(["kq_vcert10", "kq_vcert11"]);
    expect(ptSubPyr.requestedResults.map((r) => r.valueDisplay)).toEqual(["1", "1/8"]);

    // Check oblique cylinder ellipse (family12): symbolic units preserved
    const elRow = SERVED_SCENES.find((r) => r.id === "family12_cylinder_ellipse_section")!;
    const ptEl = phanTichToanHocCuaCanh(withSubEntities(elRow.scene!), null, elRow.route_d);
    expect(ptEl.requestedResults.map((r) => r.valueDisplay)).toEqual(["4π√2a^2", "24πa^3"]);
  });

  it("P8: Construction timeline starts at step 0 (given geometry), advances deterministically, and never leaks final answers in step narrations", () => {
    expect(taoTrangThai().current_step).toBe(0);
    for (const row of SERVED_SCENES) {
      const scene = withSubEntities(row.scene!);
      const gCount = geometryStepCount(scene);
      expect(gCount, `${row.id} geometryStepCount`).toBeGreaterThanOrEqual(2);
      const list = geometryStepList(scene);
      expect(list.length).toBe(gCount);
      expect(geometryAnchor(scene, 0)).toBe(list[0].anchor);

      const pt = phanTichToanHocCuaCanh(scene, null, row.route_d);
      const finalResultIds = new Set(pt.requestedResults.map((r) => r.entityId).filter(Boolean));
      for (const item of list) {
        const narr = geometryNarrationAt(scene, item.anchor);
        expect(narr.length).toBeGreaterThan(0);
        for (const fid of finalResultIds) {
          expect(narr).not.toContain(String(fid));
        }
      }
    }
  });

  it("P8 & P10: Invalid or non-intersecting geometry returns a truthful structured refusal (ERROR_OR_REFUSAL) without rendering a misleading 3D canvas", () => {
    const refusalRow = AUDIT_SCENES.find((r) => r.id === "family13_invalid_geometry_refusal")!;
    expect(refusalRow.served).toBe(false);
    expect(refusalRow.scene).toBeUndefined();
    const refusalHtml = renderToString(
      <UnsupportedNotice
        unsupported={{
          reason: refusalRow.reason ?? "Mặt phẳng không cắt mặt cầu.",
          learner_reason: refusalRow.reason ?? "Mặt phẳng cách tâm lớn hơn bán kính nên không có giao tuyến thực.",
          failure_category: "geometry_generation_failed",
          error_code: "postcondition_violated",
          stage_reached: "verification",
          refusal_cause: "SOURCE",
        }}
      />,
    );
    expect(refusalHtml).toContain("CHƯA DỰNG ĐƯỢC MÔ PHỎNG");
    expect(refusalHtml).not.toContain("geo3d-canvas");
  });
});
