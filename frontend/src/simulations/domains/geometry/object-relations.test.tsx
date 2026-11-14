import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { AxoWorkspaceV62 } from "../../../components/SimulationWorkspace";
import { GEOMETRY_SAMPLES } from "../../../data/geometry-samples";
import { clearIsolate, select, showAll, taoTrangThai } from "./interaction-state";
import { veKhongGian } from "./scene3d-chart";
import { resolveVisualPrerequisitesOf, stepCount, type Scene3D, type SceneObject } from "./scene3d-model";
import {
  buildPedagogicalConstructionPlan,
  pedagogicalStepList,
  registerExactSceneOrigin,
  resolveCanonicalSectionDesignation,
  resolveVerifiedObjectRelations,
  shortSym,
} from "./scene3d-semantic-policy";
import circumsphereFixture from "./scene3d-circumsphere-fixture.json";
import { withSubEntities } from "./scene3d-subentities";

function sampleRaw(id: string): { title: string; description: string; scene: Scene3D } {
  const s = GEOMETRY_SAMPLES.find((x) => x.id === id);
  if (!s) throw new Error(`Missing catalog sample: ${id}`);
  return {
    title: s.envelope.title ?? s.id,
    description: s.envelope.description ?? s.problemText ?? s.id,
    scene: (s.envelope as unknown as { scene3d: Scene3D }).scene3d,
  };
}

function prepareDisplayScene(raw: Scene3D): Scene3D {
  const sub = withSubEntities(raw);
  registerExactSceneOrigin(sub, raw);
  const plan = buildPedagogicalConstructionPlan(sub);
  return registerExactSceneOrigin(veKhongGian(plan.scene), plan.scene);
}

function makeSceneObj(partial: Omit<SceneObject, "origin" | "producer"> & Partial<Pick<SceneObject, "origin" | "producer">>): SceneObject {
  return {
    origin: "derived",
    producer: "test",
    ...partial,
  };
}


describe("Verified Object Relations & Context Card UI", () => {
  it("6. resolveVerifiedObjectRelations enforces strict step filtering, bidirectionality, and multi-kind coverage", () => {
    const { scene: raw } = sampleRaw("chop-thiet-dien-ba-diem");
    const disp = prepareDisplayScene(raw);
    const steps = pedagogicalStepList(disp);
    const pointM = disp.objects.find((o) => o.type === "point3" && shortSym(o) === "M")!;
    const segSa = disp.objects.find((o) => o.id === "chieu_cao_SA")
      ?? disp.objects.find((o) => o.type === "segment3" && shortSym(o) === "SA")!;
    expect(pointM).toBeDefined();
    expect(segSa).toBeDefined();

    // At step 0, future intersection/section objects must NOT leak into SA's verified relations
    const step0 = steps[0]!.anchor;
    const relSaStep0 = resolveVerifiedObjectRelations(disp, segSa.id, step0);
    const futureSection = disp.objects.find((o) => o.type === "section")!;
    expect(relSaStep0.relatedIds).not.toContain(futureSection.id);

    // At final step, M <-> S and M <-> (MNP) and SA <-> (ABCD) relations are strictly bidirectional
    const finalStep = steps[steps.length - 1]!.anchor;
    const relFromM = resolveVerifiedObjectRelations(disp, pointM.id, finalStep);
    const relFromS = resolveVerifiedObjectRelations(disp, "S", finalStep);
    const relFromSa = resolveVerifiedObjectRelations(disp, segSa.id, finalStep);
    const relFromBase = resolveVerifiedObjectRelations(disp, "day_ABCD", finalStep);
    expect(relFromM.hasVerifiedRelations).toBe(true);
    expect(relFromM.relatedIds).toContain("S");
    expect(relFromS.relatedIds).toContain(pointM.id);
    expect(relFromSa.relatedIds).toContain("day_ABCD");
    expect(relFromBase.relatedIds).toContain(segSa.id);

    // Explicit perpendicular witness bidirectional verification across line <-> plane
    const multiRelScene: Scene3D = {
      free_objects: [],
      events: [
        { step_index: 0, action: "CREATE", object: "A", depends: [], explanation: "Dựng A." },
        { step_index: 1, action: "CREATE", object: "B", depends: [], explanation: "Dựng B." },
        { step_index: 2, action: "CREATE", object: "S", depends: [], explanation: "Dựng S." },
        { step_index: 3, action: "CREATE", object: "P", depends: ["A", "B"], explanation: "Dựng (P)." },
        { step_index: 4, action: "CREATE", object: "SA", depends: ["S", "A"], explanation: "Dựng SA." },
      ],
      objects: [
        makeSceneObj({ id: "A", type: "point3", render: "point_marker", label: "A", xyz: ["0", "0", "0"], depends: [] }),
        makeSceneObj({ id: "B", type: "point3", render: "point_marker", label: "B", xyz: ["4", "0", "0"], depends: [] }),
        makeSceneObj({ id: "S", type: "point3", render: "point_marker", label: "S", xyz: ["0", "0", "3"], depends: [] }),
        makeSceneObj({
          id: "P",
          type: "plane3",
          render: "surface",
          label: "(P)",
          point: ["0", "0", "0"],
          normal: ["0", "0", "1"],
          depends: ["A", "B"],
        }),
        makeSceneObj({
          id: "SA",
          type: "segment3",
          render: "segment",
          label: "SA",
          endpoints: [["0", "0", "3"], ["0", "0", "0"]],
          endpoint_ids: ["S", "A"],
          depends: ["S", "A"],
          perpendicular_witness: {
            from: "S",
            foot: ["0", "0", "0"],
            foot_id: "A",
            on: "P",
            marker: { u: ["1", "0", "0"], v: ["0", "0", "1"] },
          },
        }),
      ],
    };
    const relPerp = resolveVerifiedObjectRelations(multiRelScene, "SA", 4);
    expect(relPerp.hasVerifiedRelations).toBe(true);
    expect(relPerp.relations.some((r) => r.kind === "perpendicular")).toBe(true);
    const relPlane = resolveVerifiedObjectRelations(multiRelScene, "P", 4);
    expect(relPlane.relatedIds).toContain("SA");
    expect(relPlane.relations.some((r) => r.kind === "perpendicular")).toBe(true);

    // Zero duplicate (kind, normalizedStatement) items across catalog scenes + canonical circle3 label
    const expectNoDupRelations = (sc: Scene3D, objId: string, stepIdx: number) => {
      const res = resolveVerifiedObjectRelations(sc, objId, stepIdx);
      const keys = res.relations.map(
        (r) => `${r.kind}::${r.statement.replace(/[()]/g, "").replace(/\s+/g, " ").trim().toLowerCase()}`,
      );
      expect(new Set(keys).size, `${objId} had duplicate relations: ${JSON.stringify(keys)}`).toBe(keys.length);
      return res;
    };
    expectNoDupRelations(disp, segSa.id, finalStep);
    expectNoDupRelations(disp, futureSection.id, finalStep);

    const cubeDisp = prepareDisplayScene(sampleRaw("lap-phuong-thiet-dien-bat-ky").scene);
    const cubeSteps = pedagogicalStepList(cubeDisp);
    const cubeLast = cubeSteps[cubeSteps.length - 1]!.anchor;
    const cubeSec = cubeDisp.objects.find((o) => o.type === "section")!;
    const relCubeSec = expectNoDupRelations(cubeDisp, cubeSec.id, cubeLast);
    const cubeVertRels = relCubeSec.relations.filter((r) => r.kind === "section_membership" && r.statement.startsWith("Đỉnh "));
    expect(cubeVertRels.length).toBe(6);

    const oxyzDisp = prepareDisplayScene(sampleRaw("oxyz-giao-diem-duong-mat").scene);
    const oxyzSteps = pedagogicalStepList(oxyzDisp);
    const oxyzLast = oxyzSteps[oxyzSteps.length - 1]!.anchor;
    expectNoDupRelations(oxyzDisp, "M", oxyzLast);

    const secantDisp = prepareDisplayScene(sampleRaw("mat-cau-cat-mat-phang").scene);
    const secantSteps = pedagogicalStepList(secantDisp);
    const secantLast = secantSteps[secantSteps.length - 1]!.anchor;
    const secantCircle = secantDisp.objects.find((o) => o.type === "circle3")!;
    const relCircle = expectNoDupRelations(secantDisp, secantCircle.id, secantLast);
    expect(relCircle.objectLabel).toContain("(H; HM)");
  });

  it("7. resolveVerifiedObjectRelations returns honest empty state when object has no verified relations (no 2D guesswork)", () => {
    const isolatedScene: Scene3D = {
      free_objects: [],
      events: [
        { step_index: 0, action: "CREATE", object: "A", depends: [], explanation: "Dựng A." },
        { step_index: 1, action: "CREATE", object: "B", depends: [], explanation: "Dựng B." },
      ],
      objects: [
        makeSceneObj({ id: "A", type: "point3", render: "point_marker", label: "A", xyz: ["0", "0", "0"], depends: [] }),
        makeSceneObj({ id: "B", type: "point3", render: "point_marker", label: "B", xyz: ["1/1000", "1/1000", "5"], depends: [] }),
      ],
    };
    const res = resolveVerifiedObjectRelations(isolatedScene, "A", 1);
    expect(res.hasVerifiedRelations).toBe(false);
    expect(res.relatedIds).toEqual([]);
    expect(res.relations).toEqual([]);
    expect(res.summaryMessage).toBe("Chưa có dữ liệu quan hệ đã xác minh cho đối tượng này");
  });

  it("12. SimulationWorkspace renders [Xem quan hệ] & [Định vị] without legacy Isolate/Hide buttons and keeps scene intact on select", () => {
    const { title, description, scene: raw } = sampleRaw("chop-thiet-dien-ba-diem");
    const disp = prepareDisplayScene(raw);
    const segSa = disp.objects.find((o) => o.id === "chieu_cao_SA")
      ?? disp.objects.find((o) => o.type === "segment3" && shortSym(o) === "SA")!;
    expect(segSa).toBeDefined();

    const html = renderToString(
      <AxoWorkspaceV62
        scene={raw}
        de={description}
        tieuDe={title}
        initialSelectedId={segSa.id}
      />,
    );
    expect(html).toContain('data-context-action="relations"');
    expect(html).toContain('aria-pressed="false"');
    expect(html).toContain("Xem quan hệ");
    expect(html).toContain('data-context-action="locate"');
    expect(html).toContain("Định vị");
    expect(html).not.toContain("Chỉ xem phần này");
    expect(html).not.toContain("Ẩn đối tượng");
    expect(html).not.toContain("Hiện lại tất cả");
    expect(html).not.toContain("Tập trung");
    expect(html).not.toContain('id="btn-card-isolate"');
    expect(html).not.toContain('id="btn-card-hide"');

    const selectedState = select(taoTrangThai(), segSa.id);
    expect(selectedState.hidden_ids).toEqual([]);
    expect(selectedState.isolated_ids).toEqual([]);
    const clearedState = showAll(clearIsolate(select(selectedState, null)));
    expect(clearedState.selected_id).toBeNull();
    expect(clearedState.hidden_ids).toEqual([]);
  });

  it("13. Architectural & CSS hygiene contracts hold in SimulationWorkspace, scene3d-view, and global.css", () => {
    const viewSrc = readFileSync(fileURLToPath(new URL("./scene3d-view.tsx", import.meta.url)), "utf8");
    const wsSrc = readFileSync(fileURLToPath(new URL("../../../components/SimulationWorkspace.tsx", import.meta.url)), "utf8");
    const cssSrc = readFileSync(fileURLToPath(new URL("../../../styles/global.css", import.meta.url)), "utf8");

    expect(wsSrc).toContain("setLocateRequest");
    expect(viewSrc).toContain("computeSmartLocateCamera");
    expect(viewSrc).toContain("durationMs = isReducedMotionActive() ? 0 : 300");
    expect(viewSrc).toContain('dieuKhien.addEventListener("start", onManualCamStart)');
    expect(viewSrc).toContain('renderer.domElement.addEventListener("wheel", onManualCamStart');
    expect(viewSrc).toContain("__geo3d_relation_highlight_ids");
    expect(viewSrc).toContain("__geo3d_locate_state");

    for (const cls of [
      ".context-action-pill--ghost",
      ".context-card-locate-status",
      ".context-card-relations-box",
      ".context-card-relation-list",
      ".context-card-relation-item",
      ".context-card-relation-badge",
      ".context-card-relation-text",
      ".context-card-relation-empty",
      ".context-relations-more-btn",
    ]) {
      expect(cssSrc).toContain(cls);
    }
  });

  it("14. V9.4.18 canonical naming consistency: MENPF and MNEPFQ match across designation, relations, and SSR workspace", () => {
    for (const [sampleId, canonName, rotatedName] of [
      ["chop-thiet-dien-ba-diem", "MENPF", "NPFME"],
      ["lap-phuong-thiet-dien-bat-ky", "MNEPFQ", "EPFQMN"],
    ] as const) {
      const { title, description, scene: raw } = sampleRaw(sampleId);
      const disp = prepareDisplayScene(raw);
      const steps = pedagogicalStepList(disp);
      const lastStep = steps[steps.length - 1]!.anchor;
      const sec = disp.objects.find((o) => o.type === "section")!;
      expect(sec).toBeDefined();
      expect(resolveCanonicalSectionDesignation(disp, sec)?.compactLabel).toBe(canonName);
      const rel = resolveVerifiedObjectRelations(disp, sec.id, lastStep);
      expect(rel.objectLabel).toBe(canonName);
      expect(rel.relations.some((r) => r.statement.includes(canonName))).toBe(true);
      expect(rel.relations.some((r) => r.statement.includes(rotatedName))).toBe(false);
      const html = renderToString(
        <AxoWorkspaceV62 scene={raw} de={description} tieuDe={title} initialSelectedId={sec.id} />,
      );
      expect(html).toContain(`Thiết diện ${canonName}`);
      expect(html).not.toContain(rotatedName);
    }
  });

  it("15. V9.4.18 certified section vertex intersections emit Giao điểm equations symmetrically without fallback wording", () => {
    const disp = prepareDisplayScene(sampleRaw("chop-thiet-dien-ba-diem").scene);
    const steps = pedagogicalStepList(disp);
    const lastStep = steps[steps.length - 1]!.anchor;
    const sec = disp.objects.find((o) => o.type === "section")!;
    const relSec = resolveVerifiedObjectRelations(disp, sec.id, lastStep);
    for (const expectedStmt of ["F = SD ∩ (MNP)", "M = SA ∩ (MNP)", "E = SB ∩ (MNP)"]) {
      const hit = relSec.relations.find((r) => r.kind === "intersection_point" && r.statement === expectedStmt);
      expect(hit, expectedStmt).toBeDefined();
      expect(hit!.kindLabel).toBe("Giao điểm");
    }
    expect(relSec.relations.some((r) => r.statement.includes("cắt cạnh SD"))).toBe(false);

    for (const [objId, expectedStmt] of [
      ["F", "F = SD ∩ (MNP)"],
      ["M", "M = SA ∩ (MNP)"],
      ["E", "E = SB ∩ (MNP)"],
      ["canh_ben_S_D", "F = SD ∩ (MNP)"],
      ["chieu_cao_SA", "M = SA ∩ (MNP)"],
      ["canh_ben_S_B", "E = SB ∩ (MNP)"],
    ] as const) {
      const res = resolveVerifiedObjectRelations(disp, objId, lastStep);
      expect(res.relations.some((r) => r.kind === "intersection_point" && r.statement === expectedStmt), `${objId} -> ${expectedStmt}`).toBe(true);
    }
    const relPlane = resolveVerifiedObjectRelations(disp, "mp_MNP", lastStep);
    for (const expectedStmt of ["F = SD ∩ (MNP)", "M = SA ∩ (MNP)", "E = SB ∩ (MNP)"]) {
      expect(relPlane.relations.some((r) => r.kind === "intersection_point" && r.statement === expectedStmt), `mp_MNP -> ${expectedStmt}`).toBe(true);
    }
  });

  it("16. V9.4.18 non-coplanarity guard rejects edges or lines lying inside the cutting plane from intersection_point", () => {
    const coplanarScene: Scene3D = {
      free_objects: [],
      events: [{ step_index: 0, action: "CREATE", object: "sec", depends: ["P"], explanation: "Dựng thiết diện." }],
      objects: [
        makeSceneObj({ id: "A", type: "point3", render: "point_marker", label: "A", xyz: ["0", "0", "0"], depends: [] }),
        makeSceneObj({ id: "B", type: "point3", render: "point_marker", label: "B", xyz: ["4", "0", "0"], depends: [] }),
        makeSceneObj({ id: "C", type: "point3", render: "point_marker", label: "C", xyz: ["4", "4", "0"], depends: [] }),
        makeSceneObj({ id: "D", type: "point3", render: "point_marker", label: "D", xyz: ["0", "4", "0"], depends: [] }),
        makeSceneObj({ id: "P_co", type: "point3", render: "point_marker", label: "Q", xyz: ["2", "0", "0"], depends: ["A", "B"] }),
        makeSceneObj({ id: "AB", type: "segment3", render: "segment", label: "AB", endpoints: [["0", "0", "0"], ["4", "0", "0"]], endpoint_ids: ["A", "B"], depends: ["A", "B"] }),
        makeSceneObj({ id: "d_co", type: "line3", render: "line", label: "d", point: ["0", "0", "0"], direction: ["1", "0", "0"], depends: ["A", "B"] }),
        makeSceneObj({ id: "I_bad", type: "point3", render: "point_marker", label: "I", xyz: ["2", "0", "0"], depends: ["d_co", "pl"] }),
        makeSceneObj({ id: "pl", type: "plane3", render: "surface", label: "(P)", point: ["0", "0", "0"], normal: ["0", "0", "1"], depends: ["A", "B", "C"] }),
        makeSceneObj({
          id: "S_box", type: "solid", render: "mesh", label: "ABCD",
          vertices: [["0", "0", "0"], ["4", "0", "0"], ["4", "4", "0"], ["0", "4", "0"]],
          vertex_ids: ["A", "B", "C", "D"], faces: [[0, 1, 2, 3]], depends: ["A", "B", "C", "D"],
        }),
        makeSceneObj({
          id: "sec", type: "section", render: "polygon", label: "Thiết diện QBC",
          polygon: [["2", "0", "0"], ["4", "0", "0"], ["4", "4", "0"]],
          ordered_vertex_symbols: ["Q", "B", "C"], ordered_vertex_ids: ["P_co", "B", "C"],
          vertex_sources: [{ kind: "SOLID_EDGE_INTERSECTION", solid_edge_vertex_indices: [0, 1] }],
          depends: ["S_box", "pl"],
        }),
      ],
    };
    const relPoint = resolveVerifiedObjectRelations(coplanarScene, "I_bad", 0);
    expect(relPoint.relations.some((r) => r.kind === "intersection_point")).toBe(false);
    const relEdge = resolveVerifiedObjectRelations(coplanarScene, "AB", 0);
    expect(relEdge.relations.some((r) => r.kind === "intersection_point")).toBe(false);
  });

  it("17. V9.4.18 measured_quantity emits perpendicular only when certified_relation === perpendicular_lines, never from raw value 0", () => {
    const makeMqScene = (certified: "perpendicular_lines" | null): Scene3D => ({
      free_objects: [],
      events: [
        { step_index: 0, action: "CREATE", object: "A", depends: [], explanation: "Dựng A." },
        { step_index: 1, action: "CREATE", object: "B", depends: [], explanation: "Dựng B." },
        { step_index: 2, action: "CREATE", object: "C", depends: [], explanation: "Dựng C." },
        { step_index: 3, action: "CREATE", object: "d1", depends: ["A", "B"], explanation: "Dựng AB." },
        { step_index: 4, action: "CREATE", object: "d2", depends: ["A", "C"], explanation: "Dựng AC." },
        { step_index: 5, action: "MEASURE", object: "q_dot", depends: ["d1", "d2"], explanation: "Đo tích vô hướng." },
      ],
      objects: [
        makeSceneObj({ id: "A", type: "point3", render: "point_marker", label: "A", xyz: ["0", "0", "0"], depends: [] }),
        makeSceneObj({ id: "B", type: "point3", render: "point_marker", label: "B", xyz: ["2", "0", "0"], depends: [] }),
        makeSceneObj({ id: "C", type: "point3", render: "point_marker", label: "C", xyz: ["0", "3", "0"], depends: [] }),
        makeSceneObj({ id: "d1", type: "segment3", render: "segment", label: "AB", endpoints: [["0", "0", "0"], ["2", "0", "0"]], endpoint_ids: ["A", "B"], depends: ["A", "B"] }),
        makeSceneObj({ id: "d2", type: "segment3", render: "segment", label: "AC", endpoints: [["0", "0", "0"], ["0", "3", "0"]], endpoint_ids: ["A", "C"], depends: ["A", "C"] }),
        makeSceneObj({
          id: "q_dot", type: "quantity", render: "readout", label: "Đại lượng đo", value: "0", depends: ["d1", "d2"],
          measured_quantity: { quantity_kind: "angle_cos", subject_ids: ["d1", "d2"], value: "0", certified_relation: certified },
        }),
      ],
    });
    const certRes = resolveVerifiedObjectRelations(makeMqScene("perpendicular_lines"), "d1", 5);
    expect(certRes.relations.some((r) => r.kind === "perpendicular" && r.statement.includes("AB ⊥ AC"))).toBe(true);
    const certPeer = resolveVerifiedObjectRelations(makeMqScene("perpendicular_lines"), "d2", 5);
    expect(certPeer.relations.some((r) => r.kind === "perpendicular")).toBe(true);
    const uncertRes = resolveVerifiedObjectRelations(makeMqScene(null), "d1", 5);
    expect(uncertRes.relations.some((r) => r.kind === "perpendicular")).toBe(false);
  });

  it("18. V9.4.18 resolveVisualPrerequisitesOf resolves visual ancestors and filters non-visual carriers from relations", () => {
    const circumScene = circumsphereFixture as unknown as Scene3D;
    const aPrime = circumScene.objects.find((o) => o.id === "A_prime")!;
    expect(aPrime).toBeDefined();
    const prereqs = resolveVisualPrerequisitesOf(circumScene, aPrime);
    expect(prereqs).toContain("A");
    expect(prereqs).toContain("B");
    expect(prereqs).toContain("O");
    expect(prereqs).not.toContain("vec_OB");

    // Mark vec_OB explicitly non_visual and confirm relations expose only visual prerequisites, never vec_OB
    const scWithNonVisCarrier: Scene3D = {
      ...circumScene,
      objects: circumScene.objects.map((o) => (o.id === "vec_OB" ? { ...o, render: "non_visual" as const, display_role: "non_visual" as const } : o)),
    };
    const lastStep = Math.max(0, stepCount(scWithNonVisCarrier) - 1);
    const relAPrime = resolveVerifiedObjectRelations(scWithNonVisCarrier, "A_prime", lastStep);
    expect(relAPrime.relatedIds).not.toContain("vec_OB");
    expect(relAPrime.relatedIds.some((id) => ["A", "B", "O"].includes(id))).toBe(true);
    expect(relAPrime.relations.some((r) => r.kind === "dependency")).toBe(true);
    const depRel = relAPrime.relations.find((r) => r.kind === "dependency")!;
    expect(depRel.kindLabel).toBe("Quan hệ phụ thuộc dựng hình");
  });

  it("19. V9.4.18 4-tier pedagogical ranking, deterministic Vietnamese ordering, and distinct-kind preservation", () => {
    const disp = prepareDisplayScene(sampleRaw("chop-thiet-dien-ba-diem").scene);
    const steps = pedagogicalStepList(disp);
    const lastStep = steps[steps.length - 1]!.anchor;
    const relSa = resolveVerifiedObjectRelations(disp, "chieu_cao_SA", lastStep);
    const perpIdx = relSa.relations.findIndex((r) => r.kind === "perpendicular");
    const pointOnLineIdx = relSa.relations.findIndex((r) => r.kind === "point_on_line");
    expect(perpIdx).toBeGreaterThanOrEqual(0);
    expect(pointOnLineIdx).toBeGreaterThanOrEqual(0);
    expect(perpIdx).toBeLessThan(pointOnLineIdx);
    // Preserve both perpendicular and intersection/containment kinds when the same pair carries distinct verified roles
    const pairKinds = new Set(relSa.relations.map((r) => r.kind));
    expect(pairKinds.size).toBeGreaterThanOrEqual(3);
    // Determinism across repeated calls
    const relSaAgain = resolveVerifiedObjectRelations(disp, "chieu_cao_SA", lastStep);
    expect(relSaAgain.relations).toEqual(relSa.relations);
  });

  it("20. V9.4.18 relations card enforces initial 4-item inline limit with #btn-context-toggle-more-relations", () => {
    const { title, description, scene: raw } = sampleRaw("chop-thiet-dien-ba-diem");
    const disp = prepareDisplayScene(raw);
    const steps = pedagogicalStepList(disp);
    const lastStep = steps[steps.length - 1]!.anchor;
    const sec = disp.objects.find((o) => o.type === "section")!;
    const rels = resolveVerifiedObjectRelations(disp, sec.id, lastStep);
    expect(rels.relations.length).toBeGreaterThan(4);

    const html = renderToString(
      <AxoWorkspaceV62 scene={raw} de={description} tieuDe={title} initialSelectedId={sec.id} />,
    );
    expect(html).toContain(`Thiết diện ${resolveCanonicalSectionDesignation(disp, sec)!.compactLabel}`);
    expect(html).toContain(`data-context-action="relations"`);

    const wsSrc = readFileSync(fileURLToPath(new URL("../../../components/SimulationWorkspace.tsx", import.meta.url)), "utf8");
    expect(wsSrc).toContain("const INITIAL_VISIBLE_RELATIONS = 4;");
    expect(wsSrc).toContain(`id="btn-context-toggle-more-relations"`);
    expect(wsSrc).toContain("aria-expanded={relationsExpanded}");
    expect(wsSrc).toContain("`Xem thêm ${hiddenCount} quan hệ`");
  });

  it("21. V9.4.18 sphere tangent & secant scenes never emit self-referential or duplicate bare/point tangency relations", () => {
    const selfRelRe = /^(.+?)\s+(?:⊥|∥|tiếp xúc|∈|⊂|=)\s+\1$/iu;
    const selfInterRe = /^(.+?)\s+là giao của\s+\1\b/iu;

    for (const sampleId of ["mat-phang-tiep-xuc-mat-cau", "mat-cau-cat-mat-phang"] as const) {
      const disp = prepareDisplayScene(sampleRaw(sampleId).scene);
      const steps = pedagogicalStepList(disp);
      const lastStep = steps[steps.length - 1]!.anchor;
      for (const obj of disp.objects) {
        const res = resolveVerifiedObjectRelations(disp, obj.id, lastStep);
        for (const rel of res.relations) {
          expect(rel.statement, `${sampleId}:${obj.id}`).not.toMatch(selfRelRe);
          expect(rel.statement, `${sampleId}:${obj.id}`).not.toMatch(selfInterRe);
        }
      }
    }

    const tanDisp = prepareDisplayScene(sampleRaw("mat-phang-tiep-xuc-mat-cau").scene);
    const tanSteps = pedagogicalStepList(tanDisp);
    const tanLast = tanSteps[tanSteps.length - 1]!.anchor;

    const tanPlaneRel = resolveVerifiedObjectRelations(tanDisp, "mp_tiep_dien", tanLast);
    expect(tanPlaneRel.relations.some((r) => r.statement === "Mặt phẳng qua A và vuông góc với IA tiếp xúc (S) tại A")).toBe(true);
    expect(tanPlaneRel.relations.some((r) => r.statement === "IA ⊥ mặt phẳng qua A và vuông góc với IA")).toBe(true);
    expect(tanPlaneRel.relations.some((r) => r.statement === "A ∈ mặt phẳng qua A và vuông góc với IA")).toBe(true);
    expect(tanPlaneRel.relations.filter((r) => r.kind === "tangency").length).toBeLessThanOrEqual(1);
    expect(tanPlaneRel.relations.some((r) => r.statement.includes("IA tiếp xúc IA") || r.statement.includes("IA ⊥ IA"))).toBe(false);

    const iaObj = tanDisp.objects.find((o) => o.id === "doan_IA" || (o.type === "segment3" && shortSym(o) === "IA"))!;
    expect(iaObj).toBeDefined();
    const iaRel = resolveVerifiedObjectRelations(tanDisp, iaObj.id, tanLast);
    expect(iaRel.relations.some((r) => r.kind === "perpendicular" && r.targetIds.includes("mp_tiep_dien"))).toBe(true);
    expect(iaRel.relations.some((r) => r.statement.startsWith("IA tiếp xúc"))).toBe(false);

    const secDisp = prepareDisplayScene(sampleRaw("mat-cau-cat-mat-phang").scene);
    const secSteps = pedagogicalStepList(secDisp);
    const secLast = secSteps[secSteps.length - 1]!.anchor;
    const cauRel = resolveVerifiedObjectRelations(secDisp, "cau", secLast);
    expect(cauRel.relations.some((r) => r.statement === "Đường tròn (H; HM) là giao của (S) và (P)")).toBe(true);
  });
});
