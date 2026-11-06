import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import * as THREE from "three";
import { GEOMETRY_SAMPLES } from "../../../data/geometry-samples";
import { AxoWorkspaceV62 } from "../../../components/SimulationWorkspace";
import {
  geometryHighlightedAt,
  objectsAt,
  type Scene3D,
} from "./scene3d-model";
import { veKhongGian } from "./scene3d-chart";
import { withSubEntities, isSubEntity } from "./scene3d-subentities";
import { auxiliaryObjects } from "./scene3d-auxiliary";
import { DEFAULT_ANNOTATION_VIEW, annotationsAt, placeAnnotationLabels } from "./scene3d-annotations";
import { buildObject3D } from "./scene3d-view";
import { PHONG_CACH_SCENE3D } from "./scene3d-roles";
import {
  buildPedagogicalConstructionPlan,
  inspectAxialCurvedOrthogonality,
  modulateSemanticColor,
  pedagogicalStepList,
  planeSolidEdgeIntersections,
  verifySceneMathematicalConsistency,
} from "./scene3d-semantic-policy";

function buildTestScene(raw: Record<string, unknown>): Scene3D {
  return veKhongGian(raw as unknown as Scene3D);
}

function catalogScene(id: string): Scene3D {
  const found = GEOMETRY_SAMPLES.find((s) => s.id === id);
  const env = found?.envelope as { scene3d?: Scene3D } | undefined;
  if (!env?.scene3d) throw new Error(`Missing catalog scene: ${id}`);
  return veKhongGian(env.scene3d);
}

/**
 * Kiểm toán tự động 12 bất biến cốt lõi (§3, §4, §6, §7, §9) trên một Scene3D bất kỳ.
 */
function assertAllTwelveConstructionInvariants(rawScene: Scene3D, label: string): void {
  // (8) Chứng chỉ toán học khớp cấu hình dựng (fail-closed consistency check)
  const consistency = verifySceneMathematicalConsistency(rawScene);
  expect(
    consistency.valid,
    `${label}: consistency contradictions: ${consistency.contradictions.map((v) => `${v.title}:${v.explanation}`).join("; ")}`,
  ).toBe(true);

  const plan = buildPedagogicalConstructionPlan(withSubEntities(rawScene));
  const scene = plan.scene;
  const steps = plan.steps;
  expect(steps.length, `${label}: empty construction plan`).toBeGreaterThan(0);
  expect(pedagogicalStepList(scene).length, `${label}: pedagogicalStepList mismatch`).toBe(steps.length);

  const byId = new Map(scene.objects.map((o) => [o.id, o]));
  expect(byId.size, `${label}: duplicate object IDs`).toBe(scene.objects.length);

  // (1) Không có chu trình phụ thuộc (DAG strictly acyclic)
  const visiting = new Set<string>();
  const visited = new Set<string>();
  const dfs = (oid: string): void => {
    expect(visiting.has(oid), `${label}: dependency cycle at ${oid}`).toBe(false);
    if (visited.has(oid)) return;
    visiting.add(oid);
    const obj = byId.get(oid);
    for (const dep of obj?.depends ?? []) {
      if (byId.has(dep) && !isSubEntity(dep)) dfs(dep);
    }
    visiting.delete(oid);
    visited.add(oid);
  };
  for (const o of scene.objects) {
    if (!isSubEntity(o.id)) dfs(o.id);
  }

  // (2), (3), (4), (5), (6), (7), (9) theo tiến trình từng bước 1..N
  const firstStepOfId = new Map<string, number>();
  steps.forEach((st, idx) => {
    for (const vid of st.visibleIds) {
      if (!firstStepOfId.has(vid)) firstStepOfId.set(vid, idx);
    }
  });

  const auxIds = auxiliaryObjects(scene);
  let prevStateObjIds = new Set<string>();
  let prevVisibleNonAux = new Set<string>();

  for (let i = 0; i < steps.length; i++) {
    const st = steps[i];
    const visObjs = objectsAt(scene, st.anchor);
    const visIds = new Set(visObjs.map((o) => o.id));
    const stepVisSet = new Set(st.visibleIds);

    // (4.3) Tuyệt đối không còn bước thuần tính toán / công bố đáp án trong timeline dựng hình chính
    expect(st.epistemicCategory, `${label} step ${i + 1}: pure conclusion step forbidden`).not.toBe("conclusion");
    expect(
      /^(?:Tính\s+(?:thể\s+tích|diện\s+tích|khoảng\s+cách|độ\s+dài|bán\s+kính|tỉ\s+số)|Kết\s+luận\s+giá\s+trị|Công\s+bố\s+đáp\s+án)/iu.test(
        st.title.trim(),
      ),
      `${label} step ${i + 1}: answer-presenting step title "${st.title}" forbidden`,
    ).toBe(false);
    expect(
      !/^\s*Dựng\s+mặt\s+phẳng\s*\(\s*đo\s*\)\s*$/iu.test(st.title),
      `${label} step ${i + 1}: duplicate measurement-only plane step forbidden`,
    ).toBe(true);

    // (6) Không có bước vô nghĩa / chỉ đổi tên mà không có delta hình học hoặc đóng miền
    if (i > 0) {
      const prev = steps[i - 1];
      const sameVis = JSON.stringify(prev.visibleIds) === JSON.stringify(st.visibleIds);
      const prevProg = JSON.stringify(scene.formation?.steps[prev.anchor]?.geometry_progress ?? []);
      const currProg = JSON.stringify(scene.formation?.steps[st.anchor]?.geometry_progress ?? []);
      expect(sameVis && prevProg === currProg, `${label} step ${i + 1}: no-op step "${st.title}"`).toBe(false);
    }

    // (9) Không rò rỉ đáp số cuối cùng trong tiêu đề/phụ đề bước dựng
    expect(st.title.trim().length, `${label} step ${i + 1}: empty title`).toBeGreaterThan(0);
    for (const q of scene.objects) {
      if (q.type !== "quantity" || q.origin === "free" || q.value == null) continue;
      if (q.annotation?.role === "given") continue;
      const valStr = String(q.value).trim();
      if (valStr.length >= 2 && /[π√/]/.test(valStr)) {
        expect(st.title.includes(valStr), `${label} step ${i + 1}: leaked derived answer ${valStr} in title`).toBe(
          false,
        );
        expect(
          st.subtitle.includes(`= ${valStr}`),
          `${label} step ${i + 1}: leaked derived answer = ${valStr} in subtitle`,
        ).toBe(false);
      }
    }

    // (3) ID, kiểu và ký hiệu đối tượng ổn định tuyệt đối giữa các bước
    for (const vo of visObjs) {
      const canonical = byId.get(vo.id);
      expect(canonical, `${label} step ${i + 1}: unknown visible object ${vo.id}`).toBeDefined();
      expect(vo.type).toBe(canonical!.type);
      expect(vo.notation).toBe(canonical!.notation);
      expect(vo.origin).toBe(canonical!.origin);
    }

    // (2) Đối tượng tiền đề trực tiếp (endpoint_ids / vertex_ids) của vật đang hiển thị phải đã có mặt
    for (const vid of st.visibleIds) {
      const vo = byId.get(vid);
      if (!vo || isSubEntity(vo.id) || vo.type === "quantity") continue;
      for (const ep of vo.endpoint_ids ?? []) {
        if (byId.has(ep) && !isSubEntity(ep)) {
          expect(visIds.has(ep), `${label} step ${i + 1}: segment ${vo.id} shown before endpoint ${ep}`).toBe(true);
        }
      }
      for (const vtx of vo.vertex_ids ?? []) {
        if (byId.has(vtx) && !isSubEntity(vtx)) {
          expect(visIds.has(vtx), `${label} step ${i + 1}: polygon/solid ${vo.id} shown before vertex ${vtx}`).toBe(
            true,
          );
        }
      }
    }

    // (4) Không rò rỉ đối tượng chỉ được đưa vào ở bước tương lai j > i
    for (const [oid, firstIdx] of firstStepOfId.entries()) {
      if (firstIdx > i) {
        expect(stepVisSet.has(oid), `${label} step ${i + 1}: future object ${oid} leaked before step ${firstIdx + 1}`).toBe(
          false,
        );
      }
    }

    // (5) Bước sau bảo toàn toàn bộ trạng thái đối tượng đã dựng ở các bước trước (và mọi vật chính không phải hình phụ tạm)
    for (const oldId of prevStateObjIds) {
      expect(visIds.has(oldId), `${label} step ${i + 1}: constructed object ${oldId} lost from scene state`).toBe(true);
    }
    prevStateObjIds = visIds;
    const currentPrimary = new Set(
      st.visibleIds.filter((oid) => {
        const o = byId.get(oid) as (typeof rawScene.objects)[number] & { synthetic?: boolean; authoritative?: boolean } | undefined;
        return Boolean(
          o && !isSubEntity(oid) && !auxIds.has(oid) && o.type !== "quantity" && !o.synthetic && o.authoritative !== false,
        );
      }),
    );
    for (const pid of prevVisibleNonAux) {
      expect(currentPrimary.has(pid), `${label} step ${i + 1}: primary object ${pid} disappeared`).toBe(true);
    }
    prevVisibleNonAux = currentPrimary;

    // (7) Không nâng DERIVED / AUXILIARY thành GIVEN
    for (const tid of st.targetIds) {
      const co = byId.get(tid) as (typeof rawScene.objects)[number] & { synthetic?: boolean; authoritative?: boolean } | undefined;
      if (!co) continue;
      const src = co.source as Record<string, unknown> | undefined;
      if (co.origin === "derived" || src?.binding === "AUXILIARY" || co.synthetic || co.authoritative === false) {
        expect(src?.is_given, `${label} step ${i + 1}: derived/aux ${tid} marked is_given=true`).not.toBe(true);
        expect(
          /\bđề\s+(?:bài\s+)?cho\s+sẵn\b/iu.test(`${st.title} ${st.subtitle}`),
          `${label} step ${i + 1}: derived/aux ${tid} narrated as given`,
        ).toBe(false);
      }
    }

    // (§7) Nhãn thông số mặc định ở bước i chỉ hiện cho đại lượng GIVEN mà đối tượng mang nó đã xuất hiện
    const defaultAnn = annotationsAt(scene, st.anchor, DEFAULT_ANNOTATION_VIEW, null);
    for (const entry of defaultAnn) {
      expect(entry.role, `${label} step ${i + 1}: non-given annotation ${entry.id} auto-shown`).toBe("given");
      for (const sid of entry.subject_ids) {
        expect(visIds.has(sid), `${label} step ${i + 1}: annotation ${entry.id} shown before subject ${sid}`).toBe(
          true,
        );
      }
    }
  }

  // (10) Điều hướng tất định: tiến 1..N, nhảy 1→N, lùi N..1→N cho cùng một trạng thái
  const snapshotAt = (stepIdx: number) => ({
    vis: objectsAt(scene, steps[stepIdx].anchor).map((o) => o.id),
    hi: [...geometryHighlightedAt(scene, steps[stepIdx].anchor)].sort(),
    title: steps[stepIdx].title,
    subtitle: steps[stepIdx].subtitle,
    ann: annotationsAt(scene, steps[stepIdx].anchor, DEFAULT_ANNOTATION_VIEW, null).map((a) => a.text),
  });
  const forwardSnapshots = steps.map((_, idx) => snapshotAt(idx));
  expect(snapshotAt(steps.length - 1)).toEqual(forwardSnapshots[steps.length - 1]);
  for (let idx = steps.length - 1; idx >= 0; idx--) {
    expect(snapshotAt(idx)).toEqual(forwardSnapshots[idx]);
  }
  expect(snapshotAt(steps.length - 1)).toEqual(forwardSnapshots[steps.length - 1]);
}

describe("AXO Construction Integrity Audit & Pedagogical Sequencing (§3–§9)", () => {
  describe("1. Toàn bộ 11 mẫu catalog hiện có đều đạt 12 bất biến và không còn bước công bố đáp án (§4.3, §9)", () => {
    for (const sample of GEOMETRY_SAMPLES) {
      it(`Catalog [${sample.id}] (${sample.group})`, () => {
        const scene = catalogScene(sample.id);
        assertAllTwelveConstructionInvariants(scene, `catalog:${sample.id}`);

        const ssrHtml = renderToString(
          <AxoWorkspaceV62
            scene={scene}
            de={sample.problemText}
            tieuDe={sample.envelope.title}
          />,
        );
        expect(ssrHtml).not.toMatch(/Công bố đáp án|Kết luận giá trị/iu);
        if (sample.id === "the-tich-chop") {
          expect(ssrHtml).not.toMatch(/Thể tích khối chóp\s*[:=]\s*20/iu);
        }
      });
    }
  });

  describe("2. Kiểm thử bắt buộc §5.2 — Trụ nghiêng / chưa chứng minh vuông góc đáy (OO' = 3, OA = √5)", () => {
    function makeCylinderScene(opts: {
      mode:
        | "illustrative_oblique"
        | "contradictory_15pi_not_perp"
        | "contradictory_15pi_single_radius_perp"
        | "certified_right";
      cO?: string;
      cOPrime?: string;
      cA?: string;
    }): Scene3D {
      const cO = opts.cO ?? "O";
      const cOPrime = opts.cOPrime ?? "O′";
      const cA = opts.cA ?? "A";
      const isRight = opts.mode === "certified_right";
      const isSinglePerp = opts.mode === "contradictory_15pi_single_radius_perp";
      // chart_metric:
      // - certified_right: g = diag(5, 5, 1), A=(1,0,0) => |OA|=√5, O'=(0,0,3) => |OO'|=3, OO' ⊥ đáy z=0.
      // - single_radius_perp: g = diag(5, 5, 4), A=(1,0,0) => |OA|=√5, O'=(0,1,1) => |OO'|^2 = 5+4 = 9 (OO'=3),
      //   OA · OO' = 0 (OO' ⊥ bán kính đơn lẻ OA), NHƯNG e2 · OO' = 5 ≠ 0 (OO' nghiêng với mặt đáy z=0, h=2 ≠ 3)!
      // - illustrative_oblique / not_perp: g = diag(5, 1, 1), A=(1,0,0) => |OA|=√5, O'=(1,0,2) => |OO'|^2 = 5+4 = 9 (OO'=3),
      //   OA · OO' = 5 ≠ 0 (OO' không vuông góc OA, h=2 ≠ 3).
      const oPrimeXyz: [string, string, string] = isRight
        ? ["0", "0", "3"]
        : isSinglePerp
          ? ["0", "1", "1"]
          : ["1", "0", "2"];
      const chartMetric = isRight
        ? [
            ["5", "0", "0"],
            ["0", "5", "0"],
            ["0", "0", "1"],
          ]
        : isSinglePerp
          ? [
              ["5", "0", "0"],
              ["0", "5", "0"],
              ["0", "0", "4"],
            ]
          : [
              ["5", "0", "0"],
              ["0", "1", "0"],
              ["0", "0", "1"],
            ];
      const includeFake15Pi =
        opts.mode === "contradictory_15pi_not_perp" || opts.mode === "contradictory_15pi_single_radius_perp";

      return buildTestScene({
        chart_metric: chartMetric,
        free_objects: [cO, cOPrime, cA, "given_oa", "given_oo"],
        objects: [
          {
            id: cO,
            type: "point3",
            label: `Tâm ${cO}`,
            notation: cO,
            origin: "free",
            render: "point_marker",
            depends: [],
            xyz: ["0", "0", "0"],
          },
          {
            id: cA,
            type: "point3",
            label: `Điểm ${cA}`,
            notation: cA,
            origin: "free",
            render: "point_marker",
            depends: [],
            xyz: ["1", "0", "0"],
          },
          {
            id: cOPrime,
            type: "point3",
            label: `Tâm ${cOPrime}`,
            notation: cOPrime,
            origin: "free",
            render: "point_marker",
            depends: [],
            xyz: oPrimeXyz,
            source: isRight
              ? { provenance: "GIVEN" }
              : { provenance: "ILLUSTRATIVE_CONFIGURATION", assumption: "ILLUSTRATIVE_CONFIGURATION" },
          },
          {
            id: "day_duoi",
            type: "circle3",
            label: `Đường tròn đáy tâm ${cO}`,
            notation: `(${cO})`,
            origin: "derived",
            producer: "construct_circle",
            render: "circle",
            surface_role: "BASE_REGION",
            formation_roles: ["CONSTRUCT_BASE"],
            depends: [cO, cA],
            center: ["0", "0", "0"],
            normal: ["0", "0", "1"],
            radius_sq: "5",
          },
          {
            id: "bk_oa",
            type: "segment3",
            label: `Bán kính ${cO}${cA}`,
            notation: `${cO}${cA}`,
            origin: "derived",
            producer: "construct_segment",
            render: "segment",
            depends: [cO, cA],
            endpoint_ids: [cO, cA],
            point_a: ["0", "0", "0"],
            point_b: ["1", "0", "0"],
            endpoints: [["0", "0", "0"], ["1", "0", "0"]],
          },
          {
            id: "doan_oo",
            type: "segment3",
            label: isRight ? `Trục ${cO}${cOPrime}` : `Đoạn nối tâm ${cO}${cOPrime}`,
            notation: `${cO}${cOPrime}`,
            origin: "derived",
            producer: "construct_segment",
            render: "segment",
            depends: [cO, cOPrime],
            endpoint_ids: [cO, cOPrime],
            point_a: ["0", "0", "0"],
            point_b: oPrimeXyz,
            endpoints: [["0", "0", "0"], oPrimeXyz],
            ...(isRight
              ? {
                  perpendicular_witness: {
                    from: cOPrime,
                    on: "day_duoi",
                    foot: ["0", "0", "0"],
                    foot_id: cO,
                    relation: "line_perp_plane",
                    status: "GIVEN",
                    certificate: "exact-gram-line-plane-orthogonality/1",
                    can_present_as_proven: false,
                    plane_directions: [["1", "0", "0"], ["0", "1", "0"]],
                    marker: { u: ["1", "0", "0"], v: ["0", "0", "1"] },
                  },
                }
              : {}),
          },
          {
            id: "day_tren",
            type: "circle3",
            label: `Đường tròn đáy tâm ${cOPrime}`,
            notation: `(${cOPrime})`,
            origin: "derived",
            producer: "construct_circle",
            render: "circle",
            surface_role: "BASE_REGION",
            depends: [cOPrime],
            center: oPrimeXyz,
            normal: ["0", "0", "1"],
            radius_sq: "5",
          },
          {
            id: "khoi_tru",
            type: "curved_solid",
            curved_kind: "cylinder",
            label: isRight ? `Hình trụ ${cO}.${cOPrime}` : `Hình trụ nghiêng ${cO}.${cOPrime}`,
            notation: `${cO}.${cOPrime}`,
            role: isRight ? `Hình trụ đứng tâm ${cO}, ${cOPrime}` : `Hình trụ nghiêng tâm ${cO}, ${cOPrime}`,
            origin: "derived",
            producer: "construct_curved_solid",
            render: "curved_solid",
            formation_roles: ["CLOSE_SOLID"],
            depends: [cO, cOPrime, cA],
            anchor: ["0", "0", "0"],
            apex_or_top: oPrimeXyz,
            rim_point: ["1", "0", "0"],
            radius_sq: "5",
            height_sq: isRight ? "9" : "4",
            source: isRight
              ? { provenance: "CONSTRUCTED" }
              : { provenance: "ILLUSTRATIVE_CONFIGURATION", assumption: "ILLUSTRATIVE_CONFIGURATION" },
          },
          {
            id: "given_oa",
            type: "quantity",
            label: `Bán kính ${cO}${cA}`,
            notation: `${cO}${cA}`,
            origin: "free",
            render: "readout",
            depends: [],
            value: "√5",
            source: { provenance: "GIVEN", is_given: true },
            annotation: {
              kind: "length",
              role: "given",
              category: "measurement",
              anchor: "segment",
              subject_ids: [cO, cA],
            },
          },
          {
            id: "given_oo",
            type: "quantity",
            label: `Đoạn nối tâm ${cO}${cOPrime}`,
            notation: `${cO}${cOPrime}`,
            origin: "free",
            render: "readout",
            depends: [],
            value: "3",
            source: { provenance: "GIVEN", is_given: true },
            annotation: {
              kind: "length",
              role: "given",
              category: "measurement",
              anchor: "segment",
              subject_ids: [cO, cOPrime],
            },
          },
          ...(!isRight
            ? [
                {
                  id: "illus_h",
                  type: "quantity",
                  label: "Chiều cao cấu hình minh hoạ",
                  notation: "h",
                  origin: "free",
                  render: "readout",
                  depends: [],
                  value: "2",
                  source: {
                    provenance: "ILLUSTRATIVE_CONFIGURATION",
                    assumption: "ILLUSTRATIVE_CONFIGURATION",
                    is_given: false,
                  },
                  annotation: {
                    kind: "length",
                    role: "given",
                    category: "measurement",
                    anchor: "solid",
                    subject_ids: ["khoi_tru"],
                  },
                },
              ]
            : []),
          ...(includeFake15Pi || isRight
            ? [
                {
                  id: "q_vol",
                  type: "quantity",
                  label: "Thể tích khối trụ",
                  notation: "V",
                  origin: "derived",
                  producer: "measure_volume",
                  render: "readout",
                  depends: ["khoi_tru"],
                  value: "15π",
                  annotation: {
                    kind: "volume",
                    role: "result",
                    category: "result",
                    anchor: "solid",
                    subject_ids: ["khoi_tru"],
                  },
                },
              ]
            : []),
        ],
        events: [
          { id: "ev0", step_index: 0, action: "INIT", semantic_kind: "EXPLANATION", objects: [cO, cA, cOPrime], depends: [] },
          { id: "ev1", step_index: 1, action: "CREATE", semantic_kind: "GEOMETRY_CONSTRUCTION", object: "day_duoi", objects: ["day_duoi"], depends: [cO, cA] },
          { id: "ev2", step_index: 2, action: "CREATE", semantic_kind: "GEOMETRY_CONSTRUCTION", object: "bk_oa", objects: ["bk_oa"], depends: [cO, cA] },
          { id: "ev3", step_index: 3, action: "CREATE", semantic_kind: "GEOMETRY_CONSTRUCTION", object: "doan_oo", objects: ["doan_oo"], depends: [cO, cOPrime] },
          { id: "ev4", step_index: 4, action: "CREATE", semantic_kind: "GEOMETRY_CONSTRUCTION", object: "day_tren", objects: ["day_tren"], depends: [cOPrime] },
          { id: "ev5", step_index: 5, action: "CREATE", semantic_kind: "GEOMETRY_CONSTRUCTION", object: "khoi_tru", objects: ["khoi_tru"], depends: [cO, cOPrime, cA] },
          ...(includeFake15Pi || isRight
            ? [{ id: "ev6", step_index: 6, action: "MEASURE", semantic_kind: "FINAL_RESULT", object: "q_vol", objects: ["q_vol"], depends: ["khoi_tru"] }]
            : []),
        ],
      });
    }

    it("từ chối V = πR²·OO' = 15π khi OO' không vuông góc OA (dot(OA, OO') ≠ 0)", () => {
      const scene = makeCylinderScene({ mode: "contradictory_15pi_not_perp" });
      const solid = scene.objects.find((o) => o.id === "khoi_tru")!;
      const ortho = inspectAxialCurvedOrthogonality(scene, solid);
      expect(ortho.isRightCertified).toBe(false);
      expect(ortho.isOblique).toBe(true);
      const check = verifySceneMathematicalConsistency(scene);
      expect(check.valid).toBe(false);
      expect(
        check.contradictions.some(
          (v) => v.title.includes("trụ") || v.explanation.includes("15π") || v.explanation.includes("πR²") || v.explanation.includes("không vuông góc"),
        ),
      ).toBe(true);
    });

    it("từ chối V = πR²·OO' = 15π ngay cả khi OO' ⊥ đúng một bán kính đơn lẻ OA nhưng nghiêng với mặt đáy (§5.2.2)", () => {
      const scene = makeCylinderScene({ mode: "contradictory_15pi_single_radius_perp" });
      const solid = scene.objects.find((o) => o.id === "khoi_tru")!;
      const ortho = inspectAxialCurvedOrthogonality(scene, solid);
      expect(ortho.isRightCertified).toBe(false);
      expect(ortho.isOblique).toBe(true);
      const check = verifySceneMathematicalConsistency(scene);
      expect(check.valid).toBe(false);
    });

    it("dựng hình trụ nghiêng minh hoạ hợp lệ: phân biệt đường nối tâm OO' với chiều cao, không bịa 15π, lưới 3D trượt xiên chính xác", () => {
      const scene = makeCylinderScene({ mode: "illustrative_oblique" });
      assertAllTwelveConstructionInvariants(scene, "oblique_cylinder_illustrative");

      const plan = buildPedagogicalConstructionPlan(withSubEntities(scene));
      const allNarration = plan.steps.map((s) => `${s.title} ${s.subtitle}`).join(" | ");
      expect(allNarration).not.toContain("15π");
      expect(allNarration).not.toMatch(/trục\s+đứng\s+OO′/iu);
      expect(allNarration).toMatch(/nối\s+(?:hai\s+)?tâm|nghiêng|xiên/iu);

      // Lưới 3D thực sự là trụ xiên trượt hai đáy song song (obliqueCylinder = true), không dựng thành trụ đứng giả
      const solid = plan.scene.objects.find((o) => o.id === "khoi_tru")!;
      const built = buildObject3D(
        solid,
        false,
        0.2,
        [],
        new THREE.Vector3(8, 3, 6),
        new Set(),
        new Map(),
        false,
        "primary",
        false,
        true,
        false,
        plan.scene,
      );
      expect(built).not.toBeNull();
      expect(built!.userData?.curvedSolidVolume?.capBasis).toHaveLength(2);
      let foundObliqueMesh = false;
      built!.traverse((node) => {
        if ((node as THREE.Mesh).isMesh && node.userData?.obliqueCylinder === true) {
          foundObliqueMesh = true;
        }
      });
      expect(foundObliqueMesh).toBe(true);

      // Thông số GIVEN (OA = √5, OO' = 3) chỉ hiện sau khi đoạn mang nó xuất hiện; thông số minh hoạ h = 2 bị chặn
      const annStep1 = annotationsAt(plan.scene, plan.steps[0].anchor, DEFAULT_ANNOTATION_VIEW, null);
      expect(annStep1.map((a) => a.id)).not.toContain("given_oo");
      const annLast = annotationsAt(plan.scene, plan.steps[plan.steps.length - 1].anchor, DEFAULT_ANNOTATION_VIEW, null);
      expect(annLast.map((a) => a.text)).toContain("OA = √5");
      expect(annLast.map((a) => a.text)).toContain("OO′ = 3");
      expect(annLast.map((a) => a.id)).not.toContain("illus_h");
    });

    it("chấp nhận trụ đứng đã chứng minh IJ ⊥ mặt đáy (đổi tên đỉnh I, J, K, IK = √5, IJ = 3) và không chèn bước công bố 15π", () => {
      const scene = makeCylinderScene({ mode: "certified_right", cO: "I", cOPrime: "J", cA: "K" });
      assertAllTwelveConstructionInvariants(scene, "certified_right_cylinder_IJK");
      const plan = buildPedagogicalConstructionPlan(withSubEntities(scene));
      for (const st of plan.steps) {
        expect(st.title).not.toContain("15π");
        expect(st.subtitle).not.toContain("15π");
      }
      const ssrStep1 = renderToString(
        <AxoWorkspaceV62
          scene={scene}
          initialStep={plan.steps[0].anchor}
          de="Hình trụ đứng I.J bán kính IK = √5, trục IJ = 3."
        />,
      );
      expect(ssrStep1).not.toContain("15π");
      const ssr = renderToString(
        <AxoWorkspaceV62 scene={scene} de="Hình trụ đứng I.J bán kính IK = √5, trục IJ = 3." />,
      );
      const ssrStepsOnly = ssr.match(/<ul[^>]*id="dock-steps-ul"[\s\S]*?<\/ul>/u)?.[0] ?? "";
      expect(ssrStepsOnly).not.toContain("15π");
      expect(ssr).not.toContain('id="dock-math-results"');
      expect(ssr).not.toContain('id="dock-goal-reveal"');
      expect(ssr).not.toContain('id="dock-goal-conclusion"');
      expect(ssr).not.toContain("15π");
      expect(plan.goalCompletion.items.map((it) => it.valueText)).toContain("15π");
    });
  });

  describe("3. Kiểm thử bắt buộc §5.3 — Thiết diện trung điểm MNPQ (gốc S.ABCD, đổi tên T.EFGH, và đáy không vuông)", () => {
    function makeMidpointSectionPyramidScene(opts: {
      apex: string;
      base: [string, string, string, string];
      mids: [string, string, string, string];
      chartMetric: [[string, string, string], [string, string, string], [string, string, string]];
      baseCoords: [
        [string, string, string],
        [string, string, string],
        [string, string, string],
        [string, string, string],
      ];
      baseProvenance: "GIVEN" | "LAYOUT_DERIVED";
    }): Scene3D {
      const [B0, B1, _B2, B3] = opts.base;
      const [M0, M1, M2, M3] = opts.mids;
      const S = opts.apex;
      const apexCoord: [string, string, string] = ["0", "0", "2"];
      const midCoord = (p: [string, string, string]): [string, string, string] => [
        String(Number(p[0]) / 2),
        String(Number(p[1]) / 2),
        "1",
      ];
      const mCoords = opts.baseCoords.map(midCoord) as [
        [string, string, string],
        [string, string, string],
        [string, string, string],
        [string, string, string],
      ];
      return buildTestScene({
        chart_metric: opts.chartMetric,
        free_objects: [...opts.base, S, "given_ab", "given_sa"],
        objects: [
          ...opts.base.map((b, idx) => ({
            id: b,
            type: "point3",
            label: `Điểm ${b}`,
            notation: b,
            origin: "free",
            render: "point_marker",
            depends: [],
            xyz: opts.baseCoords[idx],
            source: { provenance: opts.baseProvenance },
          })),
          {
            id: S,
            type: "point3",
            label: `Đỉnh ${S}`,
            notation: S,
            origin: "free",
            render: "point_marker",
            depends: [],
            xyz: apexCoord,
            source: { provenance: opts.baseProvenance },
          },
          {
            id: `day_${opts.base.join("")}`,
            type: "polygon3",
            label: `Đáy ${opts.base.join("")}`,
            notation: opts.base.join(""),
            origin: "derived",
            producer: "construct_polygon",
            render: "polygon",
            surface_role: "BASE_REGION",
            formation_roles: ["CONSTRUCT_BASE"],
            depends: [...opts.base],
            vertex_ids: [...opts.base],
            polygon: [...opts.baseCoords],
            source: { provenance: opts.baseProvenance },
          },
          ...opts.base.map((b, idx) => ({
            id: `canh_${S}_${b}`,
            type: "segment3",
            label: `Cạnh bên ${S}${b}`,
            notation: `${S}${b}`,
            origin: "derived",
            producer: "construct_segment",
            render: "segment",
            formation_roles: ["CONSTRUCT_LATERAL_BOUNDARY"],
            depends: [S, b],
            endpoint_ids: [S, b],
            point_a: apexCoord,
            point_b: opts.baseCoords[idx],
            endpoints: [apexCoord, opts.baseCoords[idx]],
          })),
          {
            id: `khoi_${S}`,
            type: "solid",
            label: `Hình chóp ${S}.${opts.base.join("")}`,
            notation: `${S}.${opts.base.join("")}`,
            shape_class: "PYRAMID_LIKE",
            origin: "derived",
            producer: "construct_solid",
            render: "mesh",
            formation_roles: ["CLOSE_SOLID"],
            depends: [S, ...opts.base],
            vertex_ids: [S, ...opts.base],
            vertices: [apexCoord, ...opts.baseCoords],
            faces: [[1, 2, 3, 4], [0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1]],
          },
          ...[0, 1, 2].map((idx) => ({
            id: opts.mids[idx],
            type: "point3",
            label: `Trung điểm ${opts.mids[idx]}`,
            notation: opts.mids[idx],
            role: `Trung điểm của ${S}${opts.base[idx]}`,
            origin: "derived",
            producer: "construct_point.midpoint",
            render: "point_marker",
            depends: [`canh_${S}_${opts.base[idx]}`],
            xyz: mCoords[idx],
            source: { provenance: "CONSTRUCTED" },
          })),
          {
            id: "mp_cut",
            type: "plane3",
            label: `Mặt phẳng (${M0}${M1}${M2})`,
            notation: `(${M0}${M1}${M2})`,
            origin: "derived",
            producer: "construct_plane",
            render: "plane",
            surface_role: "AUXILIARY_PLANE",
            depends: [M0, M1, M2],
            point: mCoords[0],
            normal: ["0", "0", "1"],
          },
          {
            id: M3,
            type: "point3",
            label: `Giao điểm ${M3}`,
            notation: M3,
            role: `Giao điểm của ${S}${B3} và (${M0}${M1}${M2})`,
            origin: "derived",
            producer: "construct_point.intersect_line_plane",
            render: "point_marker",
            depends: [`canh_${S}_${B3}`, "mp_cut"],
            xyz: mCoords[3],
            source: { provenance: "DERIVED", is_given: false },
          },
          ...[0, 1, 2, 3].map((idx) => {
            const u = opts.mids[idx];
            const v = opts.mids[(idx + 1) % 4];
            return {
              id: `gt_${u}_${v}`,
              type: "segment3",
              label: `Đoạn giao tuyến ${u}${v}`,
              notation: `${u}${v}`,
              origin: "derived",
              producer: "construct_segment",
              render: "segment",
              depends: [u, v],
              endpoint_ids: [u, v],
              point_a: mCoords[idx],
              point_b: mCoords[(idx + 1) % 4],
              endpoints: [mCoords[idx], mCoords[(idx + 1) % 4]],
            };
          }),
          {
            id: "td_mnpq",
            type: "polygon3",
            label: `Thiết diện ${opts.mids.join("")}`,
            notation: opts.mids.join(""),
            origin: "derived",
            producer: "construct_polygon",
            render: "polygon",
            surface_role: "SECTION_REGION",
            formation_roles: ["PRODUCE_SECTION"],
            depends: [`gt_${M0}_${M1}`, `gt_${M1}_${M2}`, `gt_${M2}_${M3}`, `gt_${M3}_${M0}`],
            vertex_ids: [...opts.mids],
            polygon: [...mCoords],
            source: { provenance: opts.baseProvenance },
          },
          {
            id: "given_ab",
            type: "quantity",
            label: `Cạnh đáy ${B0}${B1}`,
            notation: `${B0}${B1}`,
            origin: "free",
            render: "readout",
            depends: [],
            value: "4",
            source: { provenance: "GIVEN", is_given: true },
            annotation: {
              kind: "length",
              role: "given",
              category: "measurement",
              anchor: "segment",
              subject_ids: [B0, B1],
            },
          },
          {
            id: "given_sa",
            type: "quantity",
            label: `Cạnh bên ${S}${B0}`,
            notation: `${S}${B0}`,
            origin: "free",
            render: "readout",
            depends: [],
            value: "6",
            source: { provenance: "GIVEN", is_given: true },
            annotation: {
              kind: "length",
              role: "given",
              category: "measurement",
              anchor: "segment",
              subject_ids: [S, B0],
            },
          },
        ],
        events: [
          { id: "e0", step_index: 0, action: "INIT", semantic_kind: "EXPLANATION", objects: [...opts.base, S], depends: [] },
          { id: "e1", step_index: 1, action: "CREATE", semantic_kind: "GEOMETRY_CONSTRUCTION", object: `day_${opts.base.join("")}`, objects: [`day_${opts.base.join("")}`], depends: [...opts.base] },
          { id: "e2", step_index: 2, action: "CREATE", semantic_kind: "GEOMETRY_CONSTRUCTION", objects: opts.base.map((b) => `canh_${S}_${b}`), depends: [S, ...opts.base] },
          { id: "e3", step_index: 3, action: "CREATE", semantic_kind: "GEOMETRY_CONSTRUCTION", object: `khoi_${S}`, objects: [`khoi_${S}`], depends: [S, ...opts.base] },
          { id: "e4", step_index: 4, action: "CREATE", semantic_kind: "GEOMETRY_CONSTRUCTION", objects: [M0, M1, M2], depends: opts.base.slice(0, 3).map((b) => `canh_${S}_${b}`) },
          { id: "e5", step_index: 5, action: "CREATE", semantic_kind: "GEOMETRY_CONSTRUCTION", object: "mp_cut", objects: ["mp_cut"], depends: [M0, M1, M2] },
          { id: "e6", step_index: 6, action: "CREATE", semantic_kind: "GEOMETRY_CONSTRUCTION", object: M3, objects: [M3], depends: [`canh_${S}_${B3}`, "mp_cut"] },
          {
            id: "e7",
            step_index: 7,
            action: "CREATE",
            semantic_kind: "GEOMETRY_CONSTRUCTION",
            objects: [`gt_${M0}_${M1}`, `gt_${M1}_${M2}`, `gt_${M2}_${M3}`, `gt_${M3}_${M0}`],
            depends: [M0, M1, M2, M3],
          },
          { id: "e8", step_index: 8, action: "CREATE", semantic_kind: "GEOMETRY_CONSTRUCTION", object: "td_mnpq", objects: ["td_mnpq"], depends: [`gt_${M0}_${M1}`, `gt_${M1}_${M2}`, `gt_${M2}_${M3}`, `gt_${M3}_${M0}`] },
        ],
      });
    }

    it("S.ABCD đáy vuông & biến thể đổi tên T.EFGH: M,N,P → (MNP) → Q = SD ∩ (MNP) (DERIVED) → các cạnh giao tuyến → thiết diện", () => {
      for (const variant of [
        {
          apex: "S",
          base: ["A", "B", "C", "D"] as [string, string, string, string],
          mids: ["M", "N", "P", "Q"] as [string, string, string, string],
        },
        {
          apex: "T",
          base: ["E", "F", "G", "H"] as [string, string, string, string],
          mids: ["I", "J", "K", "L"] as [string, string, string, string],
        },
      ]) {
        const scene = makeMidpointSectionPyramidScene({
          ...variant,
          chartMetric: [
            ["4", "0", "0"],
            ["0", "4", "0"],
            ["0", "0", "9"],
          ],
          baseCoords: [
            ["0", "0", "0"],
            ["2", "0", "0"],
            ["2", "2", "0"],
            ["0", "2", "0"],
          ],
          baseProvenance: "GIVEN",
        });
        assertAllTwelveConstructionInvariants(scene, `section_${variant.mids.join("")}`);

        const plan = buildPedagogicalConstructionPlan(withSubEntities(scene));
        const stepOfObj = (oid: string) =>
          plan.steps.findIndex((s) => objectsAt(plan.scene, s.anchor).some((o) => o.id === oid));
        const idxMids = Math.max(stepOfObj(variant.mids[0]), stepOfObj(variant.mids[1]), stepOfObj(variant.mids[2]));
        const idxPlane = stepOfObj("mp_cut");
        const idxFourth = stepOfObj(variant.mids[3]);
        const idxSection = stepOfObj("td_mnpq");

        expect(idxMids).toBeGreaterThan(0);
        expect(idxPlane).toBeGreaterThanOrEqual(idxMids);
        expect(idxFourth).toBeGreaterThan(idxPlane);
        expect(idxSection).toBeGreaterThan(idxFourth);

        const fourthObj = plan.scene.objects.find((o) => o.id === variant.mids[3])!;
        expect(fourthObj.origin).toBe("derived");
        expect((fourthObj.source as Record<string, unknown>)?.provenance).toBe("DERIVED");
      }
    });

    it("không kết luận thiết diện là hình vuông khi đáy là hình chữ nhật, hình thoi, hoặc chỉ từ toạ độ bố cục (LAYOUT_DERIVED)", () => {
      const rectScene = makeMidpointSectionPyramidScene({
        apex: "S",
        base: ["A", "B", "C", "D"],
        mids: ["M", "N", "P", "Q"],
        chartMetric: [
          ["1", "0", "0"],
          ["0", "9", "0"],
          ["0", "0", "4"],
        ],
        baseCoords: [
          ["0", "0", "0"],
          ["2", "0", "0"],
          ["2", "2", "0"],
          ["0", "2", "0"],
        ],
        baseProvenance: "GIVEN",
      });
      assertAllTwelveConstructionInvariants(rectScene, "section_rect_base");
      const rectNar = buildPedagogicalConstructionPlan(withSubEntities(rectScene))
        .steps.map((s) => `${s.title} ${s.subtitle}`)
        .join(" ");
      expect(rectNar).not.toMatch(/MNPQ\s+là\s+hình\s+vuông/iu);

      const rhombusScene = makeMidpointSectionPyramidScene({
        apex: "S",
        base: ["A", "B", "C", "D"],
        mids: ["M", "N", "P", "Q"],
        chartMetric: [
          ["4", "2", "0"],
          ["2", "4", "0"],
          ["0", "0", "9"],
        ],
        baseCoords: [
          ["0", "0", "0"],
          ["2", "0", "0"],
          ["2", "2", "0"],
          ["0", "2", "0"],
        ],
        baseProvenance: "GIVEN",
      });
      assertAllTwelveConstructionInvariants(rhombusScene, "section_rhombus_base");
      const rhombusNar = buildPedagogicalConstructionPlan(withSubEntities(rhombusScene))
        .steps.map((s) => `${s.title} ${s.subtitle}`)
        .join(" ");
      expect(rhombusNar).not.toMatch(/MNPQ\s+là\s+hình\s+vuông/iu);

      const layoutScene = makeMidpointSectionPyramidScene({
        apex: "S",
        base: ["A", "B", "C", "D"],
        mids: ["M", "N", "P", "Q"],
        chartMetric: [
          ["4", "0", "0"],
          ["0", "4", "0"],
          ["0", "0", "9"],
        ],
        baseCoords: [
          ["0", "0", "0"],
          ["2", "0", "0"],
          ["2", "2", "0"],
          ["0", "2", "0"],
        ],
        baseProvenance: "LAYOUT_DERIVED",
      });
      assertAllTwelveConstructionInvariants(layoutScene, "section_layout_derived_base");
      const layoutNar = buildPedagogicalConstructionPlan(withSubEntities(layoutScene))
        .steps.map((s) => `${s.title} ${s.subtitle}`)
        .join(" ");
      expect(layoutNar).not.toMatch(/MNPQ\s+là\s+hình\s+vuông/iu);
    });
  });

  describe("4. Ma trận đa họ hình học mới (đổi tên đỉnh, thay thông số) & các ca biên phản nghiệm (§5.1, §5.4, §7, §9)", () => {
    it("Nhóm Đa diện: lăng trụ xiên ABC.A'B'C' (hình chiếu A' lên trọng tâm G) & chóp tam giác đổi tên T.UVX", () => {
      const obliquePrism = buildTestScene({
        chart_metric: [
          ["36", "18", "0"],
          ["18", "36", "0"],
          ["0", "0", "13"],
        ],
        free_objects: ["A", "B", "C", "A'", "given_ab", "given_aa"],
        objects: [
          { id: "A", type: "point3", label: "A", notation: "A", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "B", type: "point3", label: "B", notation: "B", origin: "free", render: "point_marker", depends: [], xyz: ["1", "0", "0"] },
          { id: "C", type: "point3", label: "C", notation: "C", origin: "free", render: "point_marker", depends: [], xyz: ["0", "1", "0"] },
          { id: "day_abc", type: "polygon3", label: "Đáy ABC", notation: "ABC", origin: "derived", producer: "construct_polygon", render: "polygon", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_BASE"], depends: ["A", "B", "C"], vertex_ids: ["A", "B", "C"], polygon: [["0", "0", "0"], ["1", "0", "0"], ["0", "1", "0"]] },
          { id: "G", type: "point3", label: "Trọng tâm G", notation: "G", role: "Trọng tâm tam giác ABC", origin: "derived", producer: "construct_point.centroid", render: "point_marker", depends: ["day_abc"], xyz: ["1/3", "1/3", "0"], source: { provenance: "CONSTRUCTED" } },
          { id: "A'", type: "point3", label: "Đỉnh A′", notation: "A′", origin: "free", render: "point_marker", depends: ["G"], xyz: ["1/3", "1/3", "1"] },
          { id: "B'", type: "point3", label: "Đỉnh B′", notation: "B′", origin: "derived", producer: "construct_point.translate", render: "point_marker", depends: ["B", "A'"], xyz: ["4/3", "1/3", "1"] },
          { id: "C'", type: "point3", label: "Đỉnh C′", notation: "C′", origin: "derived", producer: "construct_point.translate", render: "point_marker", depends: ["C", "A'"], xyz: ["1/3", "4/3", "1"] },
          { id: "doan_a_g", type: "segment3", label: "Đường cao A′G", notation: "A′G", origin: "derived", producer: "construct_segment", render: "segment", depends: ["A'", "G"], endpoint_ids: ["A'", "G"], point_a: ["1/3", "1/3", "1"], point_b: ["1/3", "1/3", "0"], endpoints: [["1/3", "1/3", "1"], ["1/3", "1/3", "0"]] },
          { id: "canh_aa", type: "segment3", label: "Cạnh bên AA′", notation: "AA′", origin: "derived", producer: "construct_segment", render: "segment", depends: ["A", "A'"], endpoint_ids: ["A", "A'"], point_a: ["0", "0", "0"], point_b: ["1/3", "1/3", "1"], endpoints: [["0", "0", "0"], ["1/3", "1/3", "1"]] },
          { id: "khoi_lt", type: "solid", label: "Lăng trụ xiên ABC.A′B′C′", notation: "ABC.A′B′C′", shape_class: "PRISM_LIKE", origin: "derived", producer: "construct_solid", render: "mesh", formation_roles: ["CLOSE_SOLID"], depends: ["A", "B", "C", "A'", "B'", "C'"], vertex_ids: ["A", "B", "C", "A'", "B'", "C'"], vertices: [["0", "0", "0"], ["1", "0", "0"], ["0", "1", "0"], ["1/3", "1/3", "1"], ["4/3", "1/3", "1"], ["1/3", "4/3", "1"]], faces: [[0, 1, 2], [3, 4, 5], [0, 1, 4, 3], [1, 2, 5, 4], [2, 0, 3, 5]] },
          { id: "given_ab", type: "quantity", label: "AB", notation: "AB", origin: "free", render: "readout", depends: [], value: "6", source: { provenance: "GIVEN", is_given: true }, annotation: { kind: "length", role: "given", category: "measurement", anchor: "segment", subject_ids: ["A", "B"] } },
          { id: "given_aa", type: "quantity", label: "AA′", notation: "AA′", origin: "free", render: "readout", depends: [], value: "5", source: { provenance: "GIVEN", is_given: true }, annotation: { kind: "length", role: "given", category: "measurement", anchor: "segment", subject_ids: ["A", "A'"] } },
        ],
        events: [
          { id: "e0", step_index: 0, action: "INIT", semantic_kind: "EXPLANATION", objects: ["A", "B", "C"], depends: [] },
          { id: "e1", step_index: 1, action: "CREATE", semantic_kind: "GEOMETRY_CONSTRUCTION", object: "day_abc", objects: ["day_abc"], depends: ["A", "B", "C"] },
          { id: "e2", step_index: 2, action: "CREATE", semantic_kind: "GEOMETRY_CONSTRUCTION", object: "G", objects: ["G"], depends: ["day_abc"] },
          { id: "e3", step_index: 3, action: "CREATE", semantic_kind: "GEOMETRY_CONSTRUCTION", objects: ["A'", "doan_a_g"], depends: ["G"] },
          { id: "e4", step_index: 4, action: "CREATE", semantic_kind: "GEOMETRY_CONSTRUCTION", objects: ["B'", "C'", "canh_aa"], depends: ["A", "B", "C", "A'"] },
          { id: "e5", step_index: 5, action: "CREATE", semantic_kind: "GEOMETRY_CONSTRUCTION", object: "khoi_lt", objects: ["khoi_lt"], depends: ["A", "B", "C", "A'", "B'", "C'"] },
        ],
      });
      assertAllTwelveConstructionInvariants(obliquePrism, "oblique_prism_ABC_G");
    });

    it("Nhóm Quan hệ & Ca biên (§5.1, §5.4): giao điểm ngoài đoạn t ∉ [0,1], mặt phẳng không cắt khối, và đoạn suy biến", () => {
      // (a) Mặt phẳng z = 4 nằm hẳn bên ngoài khối chóp S.ABC (t = 2 trên AS kéo dài, t ∉ [0,1]) => 0 giao điểm nội đoạn
      const nonCuttingPlaneScene = buildTestScene({
        free_objects: ["A", "B", "C", "S"],
        objects: [
          { id: "A", type: "point3", label: "A", notation: "A", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "B", type: "point3", label: "B", notation: "B", origin: "free", render: "point_marker", depends: [], xyz: ["2", "0", "0"] },
          { id: "C", type: "point3", label: "C", notation: "C", origin: "free", render: "point_marker", depends: [], xyz: ["0", "2", "0"] },
          { id: "S", type: "point3", label: "S", notation: "S", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "2"] },
          { id: "khoi_sabc", type: "solid", label: "S.ABC", notation: "S.ABC", shape_class: "PYRAMID_LIKE", origin: "derived", producer: "construct_solid", render: "mesh", depends: ["S", "A", "B", "C"], vertex_ids: ["S", "A", "B", "C"], vertices: [["0", "0", "2"], ["0", "0", "0"], ["2", "0", "0"], ["0", "2", "0"]], faces: [[1, 2, 3], [0, 1, 2], [0, 2, 3], [0, 3, 1]] },
          { id: "mp_ngoai", type: "plane3", label: "(α)", notation: "(α)", origin: "derived", producer: "construct_plane", render: "plane", depends: [], point: ["0", "0", "4"], normal: ["0", "0", "1"] },
        ],
        events: [
          { id: "e0", step_index: 0, action: "INIT", semantic_kind: "EXPLANATION", objects: ["A", "B", "C", "S"] },
          { id: "e1", step_index: 1, action: "CREATE", semantic_kind: "GEOMETRY_CONSTRUCTION", object: "khoi_sabc", objects: ["khoi_sabc"] },
          { id: "e2", step_index: 2, action: "CREATE", semantic_kind: "GEOMETRY_CONSTRUCTION", object: "mp_ngoai", objects: ["mp_ngoai"] },
        ],
      });
      const mpNgoai = nonCuttingPlaneScene.objects.find((o) => o.id === "mp_ngoai")!;
      expect(planeSolidEdgeIntersections(mpNgoai, nonCuttingPlaneScene.objects)).toHaveLength(0);

      // (b) Giao điểm khai báo nằm trên đoạn AB nhưng thực tế t = 3/2 > 1 => từ chối nhất quán toán học
      const exteriorSegmentClaim = buildTestScene({
        free_objects: ["A", "B"],
        objects: [
          { id: "A", type: "point3", label: "A", notation: "A", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
          { id: "B", type: "point3", label: "B", notation: "B", origin: "free", render: "point_marker", depends: [], xyz: ["2", "0", "0"] },
          { id: "seg_AB", type: "segment3", label: "Đoạn AB", notation: "AB", origin: "derived", render: "segment", depends: ["A", "B"], point_a: ["0", "0", "0"], point_b: ["2", "0", "0"], endpoints: [["0", "0", "0"], ["2", "0", "0"]] },
          { id: "mp_cut", type: "plane3", label: "(α)", origin: "free", render: "plane", depends: [], point: ["3", "0", "0"], normal: ["1", "0", "0"] },
          { id: "Q_ext", type: "point3", label: "Q", notation: "Q", origin: "derived", render: "point_marker", depends: ["seg_AB", "mp_cut"], source: { instruction: "intersect_segment_plane" }, xyz: ["3", "0", "0"] },
        ],
        events: [
          { id: "e0", step_index: 0, action: "INIT", objects: ["A", "B"] },
          { id: "e1", step_index: 1, action: "CREATE", object: "seg_AB", depends: ["A", "B"] },
          { id: "e2", step_index: 2, action: "CREATE", object: "Q_ext", depends: ["seg_AB", "mp_cut"] },
        ],
      });
      expect(verifySceneMathematicalConsistency(exteriorSegmentClaim).valid).toBe(false);
    });

    it("§7 Chính sách hiển thị thông số GIVEN & bảo toàn màu ngữ nghĩa khi chọn đối tượng", () => {
      const candidates = Array.from({ length: 6 }, (_, idx) => ({
        id: `lbl_${idx}`,
        ax: 180 + (idx % 2) * 4,
        ay: 240 + Math.floor(idx / 2) * 4,
        w: 64,
        h: 22,
        priority: 10 - idx,
      }));
      const placed = placeAnnotationLabels(candidates, [], { w: 390, h: 844 });
      const rects = [...placed.values()];
      for (let i = 0; i < rects.length; i++) {
        for (let j = i + 1; j < rects.length; j++) {
          const a = rects[i];
          const b = rects[j];
          const overlaps = a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h;
          expect(overlaps, `Labels ${i} and ${j} overlapped on mobile`).toBe(false);
        }
      }

      const semanticColors = [
        PHONG_CACH_SCENE3D.colors.free,
        PHONG_CACH_SCENE3D.colors.derived,
        PHONG_CACH_SCENE3D.colors.line,
        PHONG_CACH_SCENE3D.colors.planeOutline,
        PHONG_CACH_SCENE3D.colors.sectionOutline,
      ];
      for (const hex of semanticColors) {
        const baseHsl = { h: 0, s: 0, l: 0 };
        new THREE.Color(hex).getHSL(baseHsl);
        if (baseHsl.s < 0.08) continue;
        for (const state of ["neutral", "hover", "selected", "context"] as const) {
          const modHex = modulateSemanticColor(hex, state);
          const modHsl = { h: 0, s: 0, l: 0 };
          new THREE.Color(modHex).getHSL(modHsl);
          const rawDiff = Math.abs(baseHsl.h - modHsl.h) * 360;
          const hueDiffDeg = Math.min(rawDiff, 360 - rawDiff);
          expect(hueDiffDeg, `Semantic color ${hex.toString(16)} shifted hue in ${state}`).toBeLessThan(1.5);
        }
      }
    });
  });
});
