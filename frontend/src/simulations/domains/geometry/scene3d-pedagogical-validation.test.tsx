/**
 * KIỂM ĐỊNH DỰNG HÌNH THEO BƯỚC SƯ PHẠM & KHẢ NĂNG TỔNG QUÁT HÓA SCENE3D
 * (AXO SCENE3D — PEDAGOGICAL CONSTRUCTION & GENERALIZATION VALIDATION)
 *
 * Kiểm chứng:
 * 1. Bước dựng đáy (Bước 1 & Bước 2): cạnh đáy #1E293B hiển thị rõ trước khi khối `solid` khép kín,
 *    đúng bề dày cạnh khối chuẩn (`w.edge`), không sinh nét đứt giả khi chưa có khối che khuất,
 *    và nhường biên sạch (`0` chủ hình trùng) từ Bước 3 trở đi.
 * 2. Bước dựng đường cao SA ⊥ (ABCD): ký hiệu góc vuông 3D định hướng vào trong hình và hiển thị ổn định
 *    qua nhiều góc camera 3D khác nhau.
 * 3. Bước xác định giao điểm Q ∈ SD: đường phụ mang cạnh SD kẹp đúng đoạn [S, D] khi Q thuộc đoạn SD
 *    (không thò đầu thừa qua S hoặc D); khi giao điểm nằm ngoài đoạn (biến thể kéo dài t > 1), tự động
 *    kéo dài tới giao điểm và thuyết minh rõ vai trò kéo dài; đường thẳng không gian chính giữ nguyên nét vô hạn.
 * 4. Bước dựng các đoạn giao tuyến & hoàn thiện thiết diện: ánh xạ đúng từng mặt bên, kiểm chứng đại số
 *    chính xác Q^3 (MN ∥ AB, NP ∥ BC, PQ ∥ CD, QM ∥ DA, Q trung điểm SD, MNPQ là hình vuông) và thuyết minh
 *    rõ cơ sở toán học của kết luận (không chỉ nêu tên hình).
 * 5. Tổng quát hóa trên toàn bộ 11 mẫu + các họ fixture đa dạng trong repo + các biến thể nhiễu hợp lệ
 *    (đáy chữ nhật AB ≠ AD, đổi tỉ lệ kích thước, cắt lệch tỉ lệ không đối xứng).
 */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { renderToStaticMarkup } from "react-dom/server";
import * as THREE from "three";
import { describe, expect, it } from "vitest";

import { AxoWorkspaceV62 } from "../../../components/SimulationWorkspace";
import { GEOMETRY_SAMPLES, geometrySampleById } from "../../../data/geometry-samples";
import { dongBoNetDayManHinh } from "./scene3d-edge-visibility";
import {
  diemChoDuong,
  diemHuuHan,
  objectsAt,
  stepCount,
  toVec3,
  type ExactVec3,
  type Scene3D,
  type SceneObject,
  type Vec3,
} from "./scene3d-model";
import { PHONG_CACH_SCENE3D } from "./scene3d-roles";
import {
  buildPedagogicalConstructionPlan,
  buildVerifiedObjectTooltip,
  classifyExactPolygonShape,
  classifySceneObjectSemantics,
  deriveExactPolygonMathBasis,
  modulateSemanticColor,
  pedagogicalStepList,
  resolveLineDisplaySpan,
  verifySceneMathematicalConsistency,
} from "./scene3d-semantic-policy";
import { entitiesPresentAt, isSubEntity, withSubEntities } from "./scene3d-subentities";
import {
  buildObject3D,
  datCoGocVuong,
  resolveStepPolygonBoundaryOwnership,
  toSangCanhChuan,
  updateCanonicalEdgeVisibility,
} from "./scene3d-view";

function loadSampleScene(id: string): Scene3D {
  const found = geometrySampleById(id);
  expect(found, `Thiếu sample ${id}`).toBeDefined();
  return structuredClone((found!.envelope as unknown as { scene3d: Scene3D }).scene3d);
}

function loadRepoFixtureMap(relFromRepoRoot: string): Record<string, Scene3D> {
  const fullPath = resolve(process.cwd(), "..", relFromRepoRoot);
  const raw = JSON.parse(readFileSync(fullPath, "utf-8"));
  const out: Record<string, Scene3D> = {};
  if (Array.isArray(raw)) {
    for (const item of raw) {
      const id = item.id ?? item.case_id ?? item.slug;
      const sc = item.scene3d ?? item.scene ?? item.envelope?.scene3d;
      if (id && sc) out[id] = sc as Scene3D;
    }
  } else if (raw && typeof raw === "object") {
    for (const [k, val] of Object.entries(raw as Record<string, any>)) {
      const sc = val?.scene3d ?? val?.scene ?? val?.envelope?.scene3d;
      if (sc) out[k] = sc as Scene3D;
    }
  }
  return out;
}

function makeCamera(pos: Vec3, target: Vec3 = [1, 1, 1]): THREE.PerspectiveCamera {
  const cam = new THREE.PerspectiveCamera(42, 16 / 10, 0.1, 200);
  cam.position.set(...pos);
  cam.lookAt(...target);
  cam.updateMatrixWorld(true);
  cam.projectionMatrix.makePerspective(-0.5, 0.5, 0.35, -0.35, 0.1, 200);
  cam.matrixWorldInverse.copy(cam.matrixWorld).invert();
  return cam;
}

describe("§3A & §3B — Bước dựng đáy & đường cao: hiển thị cạnh đáy #1E293B và ký hiệu góc vuông 3D", () => {
  it("Bước 1 & Bước 2 của S.ABCD hiển thị rõ 4 cạnh đáy #1E293B đúng bề dày cạnh khối và không chồng nét ở Bước 3", () => {
    const rawScene = loadSampleScene("thiet-dien-chop");
    const scene = withSubEntities(rawScene);
    const steps = pedagogicalStepList(scene);
    expect(steps.length).toBe(10);

    // Bước 1 (dựng đáy ABCD) và Bước 2 (dựng đường cao SA): khối `chop` chưa xuất hiện
    for (const stepIdx of [0, 1]) {
      const anchor = steps[stepIdx].anchor;
      const present = objectsAt(scene, anchor);
      expect(present.some((o) => o.id === "chop")).toBe(false);
      const baseObj = present.find((o) => o.id === "day_ABCD");
      expect(baseObj).toBeDefined();
      expect((baseObj!.boundary_edge_ids ?? []).length).toBe(4);

      const resolvedBase = resolveStepPolygonBoundaryOwnership(baseObj!, present);
      expect(resolvedBase.boundary_edge_ids).toEqual([]);

      const root = new THREE.Group();
      const fatGroup = new THREE.Group();
      const builtBase = buildObject3D(resolvedBase, false, undefined, diemHuuHan(present), undefined, new Set(), new Map(), false, "primary", false, true, false, scene);
      expect(builtBase).not.toBeNull();
      root.add(builtBase!);
      root.updateMatrixWorld(true);

      const cam = makeCamera([6, -6, 4.5], [1, 1, 0]);
      updateCanonicalEdgeVisibility(root, cam, `step-${stepIdx}`);

      const visibleBorders: THREE.Line[] = [];
      const activeHiddenBorders: THREE.Line[] = [];
      builtBase!.traverse((child) => {
        const line = child as THREE.Line;
        if (!line.isLine || !child.visible) return;
        if (line.userData?.hidden === true || line.name.endsWith(":khuat")) {
          activeHiddenBorders.push(line);
        } else if (line.name.startsWith("polygon_border:day_ABCD")) {
          visibleBorders.push(line);
        }
      });

      expect(visibleBorders.length).toBeGreaterThanOrEqual(1);
      expect(activeHiddenBorders.length).toBe(0);
      const mat = visibleBorders[0].material as THREE.LineBasicMaterial;
      expect(mat.color.getHex()).toBe(0x1e293b);

      const summary = dongBoNetDayManHinh(
        [root],
        fatGroup,
        1280,
        PHONG_CACH_SCENE3D.fatPx.referenceCanvasHeight,
        true,
        0,
      );
      expect(summary.maxVisibleEdgeWidth).toBeCloseTo(PHONG_CACH_SCENE3D.fatPx.edge, 2);
      expect(summary.maxSectionBorderWidth).toBe(0);
    }

    // Bước 4 (hoàn thiện khối chóp S.ABCD sau bước dựng khung cạnh bên): `chop` có mặt => `day_ABCD` nhường biên sạch cho `chop`
    const step3Present = objectsAt(scene, steps[3].anchor);
    expect(step3Present.some((o) => o.id === "chop")).toBe(true);
    const baseAtStep3 = step3Present.find((o) => o.id === "day_ABCD")!;
    const resolvedAtStep3 = resolveStepPolygonBoundaryOwnership(baseAtStep3, step3Present);
    expect(resolvedAtStep3.boundary_edge_ids).toEqual(baseAtStep3.boundary_edge_ids);
    const builtAtStep3 = buildObject3D(resolvedAtStep3, false);
    const step3Lines: string[] = [];
    builtAtStep3?.traverse((c) => {
      if ((c as THREE.Line).isLine) step3Lines.push(c.name);
    });
    expect(step3Lines).toEqual([]);
  });

  it("Bước 1 của chóp đáy tam giác (`vuong-goc-chop`) hiển thị đầy đủ 3 cạnh đáy #1E293B", () => {
    const scene = withSubEntities(loadSampleScene("vuong-goc-chop"));
    const steps = pedagogicalStepList(scene);
    const present = objectsAt(scene, steps[0].anchor);
    const baseObj = present.find((o) => o.surface_role === "BASE_REGION")!;
    expect(baseObj).toBeDefined();
    const resolved = resolveStepPolygonBoundaryOwnership(baseObj, present);
    expect(resolved.boundary_edge_ids).toEqual([]);
    const built = buildObject3D(resolved, false, undefined, diemHuuHan(present));
    const thay = built?.getObjectByName(`polygon_border:${baseObj.id}:thay`) as THREE.Line | undefined;
    expect(thay).toBeDefined();
    expect((thay!.material as THREE.LineBasicMaterial).color.getHex()).toBe(0x1e293b);
  });

  it("Bước 2 dựng đường cao SA ⊥ (ABCD): ký hiệu góc vuông 3D định hướng vào trong hình và ổn định qua 5 góc camera", () => {
    const scene = withSubEntities(loadSampleScene("thiet-dien-chop"));
    const steps = pedagogicalStepList(scene);
    const step2Objs = objectsAt(scene, steps[1].anchor);
    const saObj = step2Objs.find((o) => o.id === "chieu_cao_SA")!;
    expect(saObj).toBeDefined();

    // Kể cả khi u của chứng chỉ bị đổi dấu hướng ra ngoài góc A, `buildObject3D` vẫn lật u vào miền trong hình
    const flippedSa: SceneObject = {
      ...saObj,
      perpendicular_witness: {
        ...saObj.perpendicular_witness!,
        marker: {
          u: ["-2", "0", "0"],
          v: ["0", "0", "4"],
        },
      },
    };
    const diemNen = diemHuuHan(step2Objs);
    const builtSa = buildObject3D(flippedSa, false, undefined, diemNen);
    expect(builtSa).not.toBeNull();
    const marker = builtSa!.getObjectByName("perp_marker:chieu_cao_SA") as THREE.Line | undefined;
    expect(marker).toBeDefined();
    expect((marker!.material as THREE.LineBasicMaterial).depthTest).toBe(false);
    expect(marker!.renderOrder).toBe(10);

    const ud = marker!.userData.gocVuongDonVi as { foot: Vec3; u: Vec3; v: Vec3 };
    expect(ud.foot).toEqual([0, 0, 0]);
    // u hướng vào cạnh đáy (+x) và v hướng lên đỉnh S (+z), vuông góc chính xác trong 3D
    expect(ud.u[0]).toBeGreaterThan(0.99);
    expect(ud.v[2]).toBeGreaterThan(0.99);
    const dotUV = ud.u[0] * ud.v[0] + ud.u[1] * ud.v[1] + ud.u[2] * ud.v[2];
    expect(Math.abs(dotUV)).toBeLessThan(1e-9);

    const root = new THREE.Group();
    root.add(builtSa!);
    const orbitPositions: Vec3[] = [
      [8, -6, 5],
      [-7, -5, 6],
      [6, 7, 5],
      [-6, 6, 4],
      [3, -8, 7],
    ];
    for (const pos of orbitPositions) {
      const cam = makeCamera(pos, [1, 1, 1.5]);
      const shownCount = datCoGocVuong([root], cam, 760, new THREE.Vector3(1, 1, 1.5), true);
      expect(shownCount).toBe(1);
      expect(marker!.visible).toBe(true);
      marker!.updateMatrixWorld(true);
      const attr = marker!.geometry.getAttribute("position");
      const p0 = new THREE.Vector3().fromBufferAttribute(attr, 0).applyMatrix4(marker!.matrixWorld);
      const p1 = new THREE.Vector3().fromBufferAttribute(attr, 1).applyMatrix4(marker!.matrixWorld);
      const p2 = new THREE.Vector3().fromBufferAttribute(attr, 2).applyMatrix4(marker!.matrixWorld);
      const implicitFoot: Vec3 = [p0.x + p2.x - p1.x, p0.y + p2.y - p1.y, p0.z + p2.z - p1.z];
      expect(Math.hypot(implicitFoot[0], implicitFoot[1], implicitFoot[2])).toBeLessThan(1e-5);
      const leg1 = p0.clone().sub(new THREE.Vector3(...implicitFoot));
      const leg2 = p2.clone().sub(new THREE.Vector3(...implicitFoot));
      expect(Math.abs(leg1.dot(leg2))).toBeLessThan(1e-5);
    }
  });
});

describe("§3C — Bước xác định giao điểm Q & quy tắc không kéo dài giả đường phụ", () => {
  it("Bước 9 của S.ABCD: Q thuộc đoạn SD nên đường phụ `sd` kẹp đúng [D, S], không kéo dài qua S hay D", () => {
    const rawScene = loadSampleScene("thiet-dien-chop");
    const scene = withSubEntities(rawScene);
    const steps = pedagogicalStepList(scene);
    const step8 = steps[8];
    expect(step8.title).toContain("Q");
    expect(step8.subtitle).toMatch(/trung điểm Q.*SQ = QD/u);

    const visibleAt8 = objectsAt(scene, step8.anchor);
    const sdLine = visibleAt8.find((o) => o.id === "sd")!;
    const S = toVec3(visibleAt8.find((o) => o.id === "S")!.xyz!);
    const D = toVec3(visibleAt8.find((o) => o.id === "D")!.xyz!);

    const span = resolveLineDisplaySpan(scene, sdLine, visibleAt8);
    expect(span.mode).toBe("clamped_segment");
    expect(span.endpoints).not.toBeNull();
    const [e0, e1] = span.endpoints!;
    const dLen = Math.hypot(S[0] - D[0], S[1] - D[1], S[2] - D[2]);
    const spanLen = Math.hypot(e1[0] - e0[0], e1[1] - e0[1], e1[2] - e0[2]);
    expect(spanLen).toBeCloseTo(dLen, 6);

    // Dựng bằng `buildObject3D` có `sceneContext`: đầu mút nét vẽ trùng khít D và S, không thò râu hai đầu
    const builtSd = buildObject3D(
      sdLine,
      false,
      undefined,
      diemChoDuong(visibleAt8, sdLine.id),
      undefined,
      new Set(),
      new Map(),
      false,
      "primary",
      false,
      true,
      false,
      { objects: visibleAt8 },
    );
    expect(builtSd).not.toBeNull();
    const segMeta = builtSd!.userData.nonCanonicalSegment as { a: THREE.Vector3; b: THREE.Vector3 };
    expect(segMeta.a.distanceTo(segMeta.b)).toBeCloseTo(dLen, 5);
  });

  it("5 chế độ giao điểm đường–mặt: bác bỏ Q ngoài đoạn mâu thuẫn giả thiết; chấp nhận Q ngoài đoạn khi giả thiết hợp lệ (SM = 3MA, N trung điểm SB, SP = 3PC ⇒ t = 3/2); trùng mút & song song", () => {
    // (1) Mâu thuẫn toán học: giữ M, N, P là 3 trung điểm của SA, SB, SC (mặt phẳng z = 2 song song đáy ⇒ bắt buộc Q tại t = 1/2),
    // nhưng ép Q sang t = 3/2 ngoài đoạn SD ⇒ bắt buộc từ chối fail-closed kèm giải thích tiếng Việt rõ ràng!
    const contradictoryScene = loadSampleScene("thiet-dien-chop");
    const qBad = contradictoryScene.objects.find((o) => o.id === "Q")!;
    qBad.xyz = ["0", "3", "-2"];
    qBad.polygon = [["0", "3", "-2"]];

    const badCheck = verifySceneMathematicalConsistency(contradictoryScene);
    expect(badCheck.valid).toBe(false);
    expect(badCheck.contradictions.some((c) => c.objectId === "Q")).toBe(true);
    const qErr = badCheck.contradictions.find((c) => c.objectId === "Q")!;
    expect(qErr.explanation).toMatch(/trung điểm đoạn SD.*1\/2.*ngoài đoạn SD.*3\/2/u);

    const failClosedHtml = renderToStaticMarkup(
      <AxoWorkspaceV62
        scene={contradictoryScene}
        de="Cho hình chóp S.ABCD có M, N, P là trung điểm SA, SB, SC."
        tieuDe="Cảnh mâu thuẫn dữ kiện Q"
      />,
    );
    expect(failClosedHtml).toContain("data-math-contradiction");
    expect(failClosedHtml).toContain("Mâu thuẫn dữ kiện vị trí giao điểm");
    expect(failClosedHtml).not.toContain("<canvas");

    // (2) Giao điểm ngoài đoạn HỢP LỆ (t = 3/2 > 1):
    // S(0,0,4), A(0,0,0), B(2,0,0), C(2,2,0), D(0,2,0)
    // Giả thiết hợp lệ: SM = 3MA ⇒ M(0,0,1); N trung điểm SB ⇒ N(1,0,2); SP = 3PC ⇒ P(3/2, 3/2, 1).
    // Mặt phẳng (MNP): -x + y + z = 1 (normal = [-1, 1, 1], qua M(0,0,1)) cắt đường thẳng SD tại Q(0, 3, -2) (t = 3/2 > 1),
    // và cắt các cạnh đáy CD, AD tại E(1,2,0), F(0,1,0) tạo thiết diện ngũ giác MNPEF đồng phẳng chính xác!
    const validExterior = loadSampleScene("thiet-dien-chop");
    const mObj = validExterior.objects.find((o) => o.id === "M")!;
    mObj.xyz = ["0", "0", "1"];
    mObj.polygon = [["0", "0", "1"]];
    mObj.role = "Điểm chia đoạn SA theo tỉ số 3/4";

    const pObj = validExterior.objects.find((o) => o.id === "P")!;
    pObj.xyz = ["3/2", "3/2", "1"];
    pObj.polygon = [["3/2", "3/2", "1"]];
    pObj.role = "Điểm chia đoạn SC theo tỉ số 3/4";

    const mpObj = validExterior.objects.find((o) => o.id === "mp")!;
    mpObj.point = ["0", "0", "1"];
    mpObj.normal = ["-1", "1", "1"];

    const qObj = validExterior.objects.find((o) => o.id === "Q")!;
    qObj.xyz = ["0", "3", "-2"];
    qObj.polygon = [["0", "3", "-2"]];

    const secObj = validExterior.objects.find((o) => o.id === "thiet_dien")!;
    secObj.polygon = [
      ["0", "0", "1"],
      ["1", "0", "2"],
      ["3/2", "3/2", "1"],
      ["1", "2", "0"],
      ["0", "1", "0"],
    ];
    secObj.steps = [
      { face_index: 1, a: ["0", "0", "1"], b: ["1", "0", "2"] },
      { face_index: 2, a: ["1", "0", "2"], b: ["3/2", "3/2", "1"] },
      { face_index: 3, a: ["3/2", "3/2", "1"], b: ["1", "2", "0"] },
      { face_index: 0, a: ["1", "2", "0"], b: ["0", "1", "0"] },
      { face_index: 4, a: ["0", "1", "0"], b: ["0", "0", "1"] },
    ];

    const validCheck = verifySceneMathematicalConsistency(validExterior);
    expect(validCheck.valid, JSON.stringify(validCheck.contradictions)).toBe(true);

    const steps = pedagogicalStepList(validExterior);
    const step8 = steps[8];
    const visibleAt8 = objectsAt(validExterior, step8.anchor);
    const sdLine = visibleAt8.find((o) => o.id === "sd")!;

    const span = resolveLineDisplaySpan(validExterior, sdLine, visibleAt8);
    expect(span.mode).toBe("extended_ray");
    expect(span.basePointIds).toEqual(["D", "S"]);
    expect(span.extensionDirection).toBe("before_start");
    expect(span.endpoints).not.toBeNull();
    const [pA, pB] = span.endpoints!;
    // Chỉ kéo dài một phía từ S(0,0,4) qua D(0,2,0) tới Q(0,3,-2); tuyệt đối không thò qua đỉnh S (maxZ == 4)
    const maxZ = Math.max(pA[2], pB[2]);
    const minZ = Math.min(pA[2], pB[2]);
    expect(maxZ).toBeCloseTo(4, 4);
    expect(minZ).toBeLessThan(-2);
    expect(step8.subtitle).toMatch(/kéo dài|ngoài đoạn/iu);

    const tipQ = buildVerifiedObjectTooltip(validExterior, "Q", step8.anchor);
    expect(tipQ).not.toBeNull();
    expect(tipQ!.body).toMatch(/kéo dài|ngoài đoạn/iu);

    // (3) Giao điểm trùng đầu mút (t = 1, Q ≡ D): không kéo dài qua S hay D
    const coincidentScene = loadSampleScene("thiet-dien-chop");
    const pAtC = coincidentScene.objects.find((o) => o.id === "P")!;
    pAtC.xyz = ["2", "2", "0"];
    pAtC.polygon = [["2", "2", "0"]];
    pAtC.role = "Điểm trùng đầu mút C trên SC";
    const mpCoinc = coincidentScene.objects.find((o) => o.id === "mp")!;
    // Mặt phẳng qua M(0,0,2), C(2,2,0), D(0,2,0): y + z = 2 (normal = [0, 1, 1]) cắt SB tại (4/3, 0, 4/3)?
    // Lấy M(0,0,2), N(2,0,0)=B: mặt phẳng qua M(0,0,2), N(1,0,2)? Không: lấy M(0,0,2), N(4/3,0,4/3) trên SB (2x+z=4, y=0):
    // Với mặt phẳng y + z = 2: trên SB(2u, 0, 4-4u) => 4-4u = 2 => u = 1/2 => N(1,0,2) VẪN thuộc mặt phẳng y + z = 2?
    // Kiểm tra: M(0,0,2) có y+z = 2; N(1,0,2) có y+z = 2; P = C(2,2,0) có y+z = 2; D(0,2,0) có y+z = 2!!
    mpCoinc.point = ["0", "2", "0"];
    mpCoinc.normal = ["0", "1", "1"];
    const qAtD = coincidentScene.objects.find((o) => o.id === "Q")!;
    qAtD.xyz = ["0", "2", "0"];
    qAtD.polygon = [["0", "2", "0"]];
    const secCoinc = coincidentScene.objects.find((o) => o.id === "thiet_dien")!;
    secCoinc.polygon = [
      ["1", "0", "2"],
      ["0", "0", "2"],
      ["0", "2", "0"],
      ["2", "2", "0"],
    ];
    secCoinc.steps = [
      { face_index: 1, a: ["0", "0", "2"], b: ["1", "0", "2"] },
      { face_index: 2, a: ["1", "0", "2"], b: ["2", "2", "0"] },
      { face_index: 0, a: ["2", "2", "0"], b: ["0", "2", "0"] },
      { face_index: 4, a: ["0", "2", "0"], b: ["0", "0", "2"] },
    ];
    expect(verifySceneMathematicalConsistency(coincidentScene).valid).toBe(true);
    const coincSteps = pedagogicalStepList(coincidentScene);
    const coincVis8 = objectsAt(coincidentScene, coincSteps[8].anchor);
    const coincSpan = resolveLineDisplaySpan(
      coincidentScene,
      coincVis8.find((o) => o.id === "sd")!,
      coincVis8,
    );
    expect(coincSpan.mode).toBe("clamped_segment");
    expect(coincSpan.coincidentEndpointId).toBe("D");
    expect(coincSteps[8].subtitle).toMatch(/trùng D.*không cần kéo dài/u);

    // (4) Không có giao điểm hợp lệ (SD ∥ (α)): đường thẳng song song mặt phẳng cắt
    const parallelScene = loadSampleScene("thiet-dien-chop");
    const mpPar = parallelScene.objects.find((o) => o.id === "mp")!;
    // SD có chỉ phương (0, 2, -4); pháp tuyến n = (0, 2, 1) thỏa d·n = 0, đi qua B(2,0,0) nhưng không qua S(0,0,4)
    mpPar.point = ["2", "0", "0"];
    mpPar.normal = ["0", "2", "1"];
    mpPar.depends = ["B"];
    const parCheck = verifySceneMathematicalConsistency(parallelScene);
    expect(parCheck.valid).toBe(false);
    expect(parCheck.contradictions.some((c) => c.objectId === "Q" && /song song/u.test(c.explanation))).toBe(true);
    const parVis = parallelScene.objects.filter((o) => o.id !== "Q");
    const parSpan = resolveLineDisplaySpan(
      { objects: parVis },
      parVis.find((o) => o.id === "sd")!,
      parVis,
    );
    expect(parSpan.mode).toBe("no_intersection");
    expect(parSpan.endpoints).toBeNull();
    const builtParSd = buildObject3D(
      parVis.find((o) => o.id === "sd")!,
      false,
      undefined,
      [],
      undefined,
      new Set(),
      new Map(),
      false,
      "primary",
      false,
      true,
      false,
      { objects: parVis },
    );
    expect(builtParSd).toBeNull();
  });

  it("Đường thẳng không gian mục tiêu (`bc` trong `vuong-goc-chop`) giữ nguyên phần kéo dài vô hạn để phân biệt với đoạn thẳng", () => {
    const scene = loadSampleScene("vuong-goc-chop");
    const finalObjs = objectsAt(scene, stepCount(scene) - 1);
    const bcLine = finalObjs.find((o) => o.id === "bc")!;
    const B = toVec3(finalObjs.find((o) => o.id === "B")!.xyz!);
    const C = toVec3(finalObjs.find((o) => o.id === "C")!.xyz!);
    const bcSegLen = Math.hypot(C[0] - B[0], C[1] - B[1], C[2] - B[2]);

    const span = resolveLineDisplaySpan(scene, bcLine, finalObjs);
    expect(span.mode).toBe("infinite_line");
    expect(span.endpoints).not.toBeNull();
    const [e0, e1] = span.endpoints!;
    expect(Math.hypot(e1[0] - e0[0], e1[1] - e0[1], e1[2] - e0[2])).toBeGreaterThan(bcSegLen * 1.15);
  });
});

describe("§3D & §3E — Kiểm chứng toán học các giao tuyến & cơ sở kết luận thiết diện hình vuông", () => {
  it("Xác minh chính xác MN ∥ AB, NP ∥ BC, PQ ∥ CD, QM ∥ DA, Q trung điểm SD, MNPQ là hình vuông và thuyết minh rõ cơ sở toán học", () => {
    const scene = loadSampleScene("thiet-dien-chop");
    const steps = pedagogicalStepList(scene);
    expect(steps.length).toBe(10);

    // Bước 10 (index 9): dựng 4 đoạn giao tuyến trên 4 mặt bên và hoàn thiện miền thiết diện (MNPQ)
    const step9 = steps[9];
    expect(step9.subtitle).toContain("(SAB)");
    expect(step9.subtitle).toContain("MN");
    expect(step9.subtitle).toContain("(SBC)");
    expect(step9.subtitle).toContain("NP");
    expect(step9.subtitle).toContain("(SCD)");
    expect(step9.subtitle).toContain("PQ");
    expect(step9.subtitle).toMatch(/\(SAD\)|\(SDA\)/);
    expect(step9.subtitle).toContain("QM");

    // Trên cảnh mẫu legacy chưa đính chứng chỉ hình vuông cho `day_ABCD`, chỉ kết luận các cặp song song, không tự gán "hình vuông" từ tọa độ (§3.2);
    // khi `day_ABCD` mang tiền đề hình vuông đã chứng nhận, `deriveExactPolygonMathBasis` và tooltip suy dẫn đầy đủ `MNPQ` là `hình vuông`.
    const rawSecObj = scene.objects.find((o) => o.id === "thiet_dien")!;
    const rawBasis = deriveExactPolygonMathBasis(scene, rawSecObj);
    expect(rawBasis?.shape).toBe("tứ giác");

    const certScene = loadSampleScene("thiet-dien-chop");
    certScene.objects.find((o) => o.id === "day_ABCD")!.label = "Đáy ABCD là hình vuông";
    const secObj = certScene.objects.find((o) => o.id === "thiet_dien")!;
    const basis = deriveExactPolygonMathBasis(certScene, secObj);
    expect(basis).not.toBeNull();
    expect(basis!.shape).toBe("hình vuông");
    expect(basis!.parallelPairs).toEqual(
      expect.arrayContaining(["MN ∥ AB", "NP ∥ BC", "PQ ∥ CD", "QM ∥ DA"]),
    );
    expect(basis!.metricFacts.join(" ")).toContain("MN = NP = PQ = QM");
    expect(basis!.metricFacts.join(" ")).toContain("MN ⊥ NP");

    expect(step9.title).toBe("Dựng các giao tuyến và hoàn thiện thiết diện (MNPQ)");
    expect(step9.title).not.toContain("hình vuông");
    // Thuyết minh bước khép kín nêu căn cứ giao tuyến quan sát được, không tự kết luận thay học sinh trên tiêu đề bước
    expect(step9.subtitle).toContain("MN ∥ AB");
    expect(step9.subtitle).toContain("NP ∥ BC");
    expect(step9.subtitle).toContain("PQ ∥ CD");
    expect(step9.subtitle).toContain("QM ∥ DA");
    expect(step9.subtitle).not.toContain("hình vuông");

    const tipSec = buildVerifiedObjectTooltip(certScene, "thiet_dien", step9.anchor);
    expect(tipSec).not.toBeNull();
    expect(tipSec!.body).toContain("MN ∥ AB");
    expect(tipSec!.body).toContain("hình vuông");
  });
});

describe("§4 — Tổng quát hóa trên toàn bộ mẫu, các họ fixture đa dạng & biến thể nhiễu hình học", () => {
  it("Toàn bộ 11 mẫu trong `geometry-samples.json` thỏa bất biến dependency graph & không rò rỉ đối tượng tương lai", () => {
    expect(GEOMETRY_SAMPLES.length).toBe(11);
    for (const sample of GEOMETRY_SAMPLES) {
      const rawScene = (sample.envelope as unknown as { scene3d: Scene3D }).scene3d;
      const scene = withSubEntities(structuredClone(rawScene));
      const n = stepCount(scene);
      expect(n).toBeGreaterThan(0);

      for (let k = 0; k < n; k += 1) {
        const presentIds = entitiesPresentAt(scene, k, objectsAt);
        for (const obj of scene.objects) {
          if (!presentIds.has(obj.id) || isSubEntity(obj.id)) continue;
          for (const depId of obj.depends ?? []) {
            expect(
              presentIds.has(depId),
              `[${sample.id}] ở step ${k}: ${obj.id} xuất hiện trước dependency ${depId}`,
            ).toBe(true);
          }
        }
      }

      const ped = pedagogicalStepList(scene);
      expect(ped.length).toBeGreaterThan(0);
      expect(ped[ped.length - 1].anchor).toBe(n - 1);
      for (let i = 0; i < ped.length; i += 1) {
        if (i > 0) expect(ped[i].anchor).toBeGreaterThan(ped[i - 1].anchor);
        expect(ped[i].title).not.toMatch(/Plane3\(|Fraction\(|Vec3\(|construct_|intersect_|::/);
        expect(ped[i].subtitle).not.toMatch(/Plane3\(|Fraction\(|Vec3\(|construct_|intersect_|::/);
      }
    }
  });

  it("Các họ fixture đa dạng trong kho (chóp bất đối xứng, lăng trụ, nón cụt, cầu cắt mặt phẳng, trụ cắt elip, thiết diện hình thang) đều hợp lệ", () => {
    const auditScenes = loadRepoFixtureMap(
      "docs/evaluation/geometry/runs/geometric-visual-correctness-framing/demos/audit_scenes.json",
    );
    const sectionScenes = loadRepoFixtureMap(
      "docs/evaluation/geometry/runs/goal-directed-section-planning/visual/scenes.json",
    );

    const selectedFixtures: [string, Scene3D][] = [
      ["family01_triangular_pyramid", auditScenes["family01_triangular_pyramid"]],
      ["family02_quadrilateral_pyramid", auditScenes["family02_quadrilateral_pyramid"]],
      ["family04_derived_sub_pyramid", auditScenes["family04_derived_sub_pyramid"]],
      ["family05_prism", auditScenes["family05_prism"]],
      ["family08_unnamed_section_vertices", auditScenes["family08_unnamed_section_vertices"]],
      ["family10_cone_frustum_cut", auditScenes["family10_cone_frustum_cut"]],
      ["family11_sphere_plane_cut", auditScenes["family11_sphere_plane_cut"]],
      ["family12_cylinder_ellipse_section", auditScenes["family12_cylinder_ellipse_section"]],
      ["section-MAB-trapezoid", sectionScenes["section-MAB-trapezoid"]],
      ["aux-foot-S-to-BD", sectionScenes["aux-foot-S-to-BD"]],
    ];

    for (const [fid, raw] of selectedFixtures) {
      expect(raw, `Thiếu fixture ${fid}`).toBeDefined();
      const scene = withSubEntities(structuredClone(raw));
      const n = stepCount(scene);
      expect(n).toBeGreaterThan(0);

      for (let k = 0; k < n; k += 1) {
        const presentIds = entitiesPresentAt(scene, k, objectsAt);
        for (const obj of scene.objects) {
          if (!presentIds.has(obj.id) || isSubEntity(obj.id)) continue;
          for (const depId of obj.depends ?? []) {
            expect(
              presentIds.has(depId),
              `[${fid}] step ${k}: ${obj.id} thiếu dependency ${depId}`,
            ).toBe(true);
          }
        }
      }

      const ped = pedagogicalStepList(scene);
      expect(ped.length).toBeGreaterThan(0);
      expect(ped[ped.length - 1].anchor).toBe(n - 1);
    }

    // Kiểm tra riêng `section-MAB-trapezoid`: thiết diện là hình thang với cơ sở song song thực tế
    const trapScene = structuredClone(sectionScenes["section-MAB-trapezoid"]);
    const trapSec = trapScene.objects.find((o) => o.type === "section")!;
    const trapShape = classifyExactPolygonShape(trapSec.polygon!, trapScene.chart_metric);
    expect(trapShape).toMatch(/hình thang/u);
    const trapBasis = deriveExactPolygonMathBasis(trapScene, trapSec);
    expect(trapBasis).not.toBeNull();
    expect(trapBasis!.summary).toMatch(/∥/);
    expect(trapBasis!.summary).toMatch(/hình thang/u);

    // Chip đối tượng trong Study Dock không bao giờ sinh chuỗi "Thiết diện null" khi có đỉnh cắt chưa đặt tên
    const trapFull = withSubEntities(structuredClone(trapScene));
    const trapHtml = renderToStaticMarkup(
      <AxoWorkspaceV62
        scene={trapFull}
        de="Cho hình chóp S.ABCD đáy hình vuông, M là trung điểm SC. Dựng thiết diện cắt bởi mặt phẳng (MAB)."
        tieuDe="Thiết diện hình thang"
        initialStep={stepCount(trapFull) - 1}
      />,
    );
    expect(trapHtml).not.toContain("Thiết diện null");
    expect(trapHtml).toContain("Thiết diện của S.ABCD cắt bởi (MAB)");
  });

  it("Biến thể nhiễu kích thước (đáy hình chữ nhật AB = 4, AD = 2; tỉ lệ phóng đại; cắt lệch tỉ lệ): không phụ thuộc tọa độ cứng", () => {
    // 1. Đáy hình chữ nhật AB = 4, AD = 2, SA = 4 => MNPQ phải được chứng minh là HÌNH CHỮ NHẬT (MN ≠ NP), không phải hình vuông!
    const rectScene = loadSampleScene("thiet-dien-chop");
    rectScene.objects.find((o) => o.id === "day_ABCD")!.label = "Đáy ABCD là hình chữ nhật";
    const scaleX2 = (v: ExactVec3): ExactVec3 => {
      const [num, den] = v[0].includes("/") ? v[0].split("/").map(Number) : [Number(v[0]), 1];
      const n2 = num * 2;
      const val = n2 % den === 0 ? String(n2 / den) : `${n2}/${den}`;
      return [val, v[1], v[2]];
    };
    for (const o of rectScene.objects) {
      if (o.xyz) o.xyz = scaleX2(o.xyz);
      if (o.point_a) o.point_a = scaleX2(o.point_a);
      if (o.point_b) o.point_b = scaleX2(o.point_b);
      if (o.endpoints) o.endpoints = [scaleX2(o.endpoints[0]), scaleX2(o.endpoints[1])];
      if (o.vertices) o.vertices = o.vertices.map(scaleX2);
      if (o.polygon) o.polygon = o.polygon.map(scaleX2);
      if (o.steps) o.steps = o.steps.map((st) => ({ ...st, a: scaleX2(st.a), b: scaleX2(st.b) }));
    }
    const rectSteps = pedagogicalStepList(rectScene);
    expect(rectSteps[0].title).toContain("hình chữ nhật");
    const rectSec = rectScene.objects.find((o) => o.id === "thiet_dien")!;
    const rectBasis = deriveExactPolygonMathBasis(rectScene, rectSec);
    expect(rectBasis).not.toBeNull();
    expect(rectBasis!.shape).toBe("hình chữ nhật");
    expect(rectBasis!.summary).toContain("MN ∥ AB");
    expect(rectBasis!.summary).toContain("MN ⊥ NP");
    expect(rectBasis!.summary).toContain("hình chữ nhật");
    expect(rectBasis!.summary).not.toContain("hình vuông");
    expect(rectSteps[rectSteps.length - 1].subtitle).toContain("MN ∥ AB");
    expect(rectSteps[rectSteps.length - 1].subtitle).not.toContain("hình chữ nhật");
    expect(rectSteps[rectSteps.length - 1].subtitle).not.toContain("hình vuông");

    // 2. Cắt không đối xứng (mặt phẳng nghiêng cắt SA, SB, SC, SD theo các tỉ lệ khác nhau): không bịa quan hệ song song hay hình vuông
    const asymScene = loadSampleScene("thiet-dien-chop");
    // Mặt phẳng z + x/4 + y/2 = 2 đi qua:
    // M on SA(0,0,z): z = 2 => (0, 0, 2) (t=1/2)
    // N on SB(2u,0,4-4u): 4 - 4u + u/2 = 2 => 3.5u = 2 => u = 4/7 => N = (8/7, 0, 12/7)
    // P on SC(2u,2u,4-4u): 4 - 4u + u/2 + u = 2 => 2.5u = 2 => u = 4/5 => P = (8/5, 8/5, 4/5)
    // Q on SD(0,2u,4-4u): 4 - 4u + u = 2 => 3u = 2 => u = 2/3 => Q = (0, 4/3, 4/3)
    const setPt = (id: string, xyz: ExactVec3, roleText: string) => {
      const p = asymScene.objects.find((o) => o.id === id)!;
      p.xyz = xyz;
      p.polygon = [xyz];
      p.role = roleText;
    };
    const M: ExactVec3 = ["0", "0", "2"];
    const N: ExactVec3 = ["8/7", "0", "12/7"];
    const P: ExactVec3 = ["8/5", "8/5", "4/5"];
    const Q: ExactVec3 = ["0", "4/3", "4/3"];
    setPt("M", M, "Trung điểm của S và A");
    setPt("N", N, "Điểm chia đoạn SB theo tỉ số 4/7");
    setPt("P", P, "Điểm chia đoạn SC theo tỉ số 4/5");
    setPt("Q", Q, "Giao điểm của SD và (MNP)");
    const asymMp = asymScene.objects.find((o) => o.id === "mp")!;
    asymMp.point = ["0", "0", "2"];
    asymMp.normal = ["1", "2", "4"];
    const asymSec = asymScene.objects.find((o) => o.id === "thiet_dien")!;
    asymSec.polygon = [N, M, Q, P];
    asymSec.steps = [
      { face_index: 1, a: M, b: N },
      { face_index: 2, a: N, b: P },
      { face_index: 3, a: P, b: Q },
      { face_index: 4, a: Q, b: M },
    ];
    expect(verifySceneMathematicalConsistency(asymScene).valid).toBe(true);
    const asymBasis = deriveExactPolygonMathBasis(asymScene, asymSec);
    expect(asymBasis).not.toBeNull();
    expect(asymBasis!.shape).toBe("tứ giác");
    expect(asymBasis!.parallelPairs).toEqual([]);
    expect(asymBasis!.summary).not.toContain("hình vuông");
  });
});

function hueDegreesOfHex(hex: number): number {
  const c = new THREE.Color(hex);
  const hsl = { h: 0, s: 0, l: 0 };
  c.getHSL(hsl, THREE.SRGBColorSpace);
  return hsl.h * 360;
}

function hueDeltaDegrees(hexA: number, hexB: number): number {
  const d = Math.abs(hueDegreesOfHex(hexA) - hueDegreesOfHex(hexB)) % 360;
  return d > 180 ? 360 - d : d;
}

describe("§3 (Mới) — Đồ thị phụ thuộc tôpô DAG & đầy đủ 7 trường siêu dữ liệu sư phạm", () => {
  it("Ví dụ tham chiếu A (`thiet-dien-chop`): 11 bước sư phạm chuẩn (tách khung cạnh bên SB, SC, SD và khép kín mặt bên), đủ 7 trường siêu dữ liệu, không rò rỉ đối tượng bước tương lai", () => {
    const raw = loadSampleScene("thiet-dien-chop");
    const plan = buildPedagogicalConstructionPlan(withSubEntities(raw));
    expect(plan.steps.length).toBe(10);

    const titles = plan.steps.map((s) => s.title);
    // Raw legacy `thiet-dien-chop` in `geometry-samples.json` lacks base square provenance, so Step 1 honestly renders "Dựng mặt đáy ABCD" (§3.2)
    expect(titles[0]).toMatch(/Dựng mặt đáy ABCD/u);
    expect(titles[1]).toMatch(/Dựng đường cao SA ⊥ \(ABCD\) tại A/u);
    expect(titles[2]).toMatch(/Dựng các cạnh bên SB, SC, SD/u);
    expect(titles[3]).toMatch(/Hoàn thiện hình chóp S\.ABCD/iu);
    expect(titles[4]).toMatch(/Xác định trung điểm M của SA/u);
    expect(titles[5]).toMatch(/Xác định trung điểm N của SB/u);
    expect(titles[6]).toMatch(/Xác định trung điểm P của SC/u);
    expect(titles[7]).toMatch(/Dựng mặt phẳng cắt \(MNP\)/u);
    expect(titles[8]).toMatch(/Xác định giao điểm Q = SD ∩ \(MNP\)/u);
    expect(titles[9]).toBe("Dựng các giao tuyến và hoàn thiện thiết diện (MNPQ)");

    // Bước 1 chỉ có mặt đáy ABCD và 4 đỉnh A, B, C, D; chưa rò rỉ S, M, N, P, Q, (MNP), thiết diện
    const step1Vis = new Set(plan.steps[0].visibleIds);
    for (const v of ["A", "B", "C", "D", "day_ABCD"]) expect(step1Vis.has(v)).toBe(true);
    for (const futureId of ["S", "M", "N", "P", "Q", "mp", "thiet_dien", "chop"]) {
      expect(step1Vis.has(futureId)).toBe(false);
    }

    // Bước 3 dựng bộ khung cạnh bên SB, SC, SD (chưa đóng kín mặt bên `chop`); Bước 4 đóng kín khối S.ABCD nhưng chưa có M, N, P, Q
    const step3FrameVis = new Set(plan.steps[2].visibleIds);
    expect(step3FrameVis.has("canh_ben_S_B")).toBe(true);
    expect(step3FrameVis.has("chop")).toBe(false);
    const step4Vis = new Set(plan.steps[3].visibleIds);
    expect(step4Vis.has("chop")).toBe(true);
    for (const futureId of ["M", "N", "P", "Q", "mp", "thiet_dien"]) {
      expect(step4Vis.has(futureId)).toBe(false);
    }

    // Kiểm tra đầy đủ 7 trường siêu dữ liệu và bất biến tiên quyết
    const seenIds = new Set<string>(plan.scene.free_objects);
    for (const st of plan.steps) {
      expect(st.targetIds.length).toBeGreaterThan(0);
      expect(st.operation.trim().length).toBeGreaterThan(0);
      expect(st.premise.trim().length).toBeGreaterThan(0);
      expect(st.title.trim().length).toBeGreaterThan(0);
      expect(st.visibleIds.length).toBeGreaterThan(0);
      expect(["given", "derived", "constructed", "auxiliary"]).toContain(st.epistemicCategory);
      expect(["Đề cho", "Được suy ra", "Được dựng", "Hình phụ"]).toContain(st.categoryLabel);
      for (const pre of st.prerequisiteIds) {
        expect(seenIds.has(pre), `Bước ${st.index + 1} dùng tiên quyết ${pre} chưa tồn tại`).toBe(true);
      }
      for (const vId of st.visibleIds) seenIds.add(vId);
      for (const tId of st.targetIds) seenIds.add(tId);
    }
  });

  it("Ví dụ tham chiếu B (`section-MAB-trapezoid`): tự động sắp lại tôpô để dựng ABCD -> S.ABCD (có cạnh SC) trước khi lấy trung điểm M của SC, không tự bịa SA ⊥ (ABCD)", () => {
    const sectionScenes = loadRepoFixtureMap(
      "docs/evaluation/geometry/runs/goal-directed-section-planning/visual/scenes.json",
    );
    const rawMab = structuredClone(sectionScenes["section-MAB-trapezoid"]);
    // Xác nhận dữ liệu gốc trước khi sửa có M ở sự kiện số 1 (trước cả đáy ABCD và khối S.ABCD)
    expect(rawMab.events[1]?.object).toBe("M");

    const plan = buildPedagogicalConstructionPlan(withSubEntities(rawMab));
    expect(plan.reordered).toBe(true);
    expect(plan.dagEdges.some((e) => e.reason === "carrier_solid_before_edge_construction")).toBe(true);

    const titles = plan.steps.map((s) => s.title);
    expect(titles.length).toBe(6);
    // Bước 1: dựng đáy ABCD (trên raw scene chưa đính `source_provenance`, không tự gán "hình vuông"); tuyệt đối chưa hiện M hay S
    expect(titles[0]).toMatch(/Dựng mặt đáy ABCD/u);
    expect(plan.steps[0].visibleIds).toContain("day_ABCD");
    expect(plan.steps[0].visibleIds).not.toContain("M");
    expect(plan.steps[0].visibleIds).not.toContain("S");

    // Bước 2: dựng bộ khung các cạnh bên SA, SB, SC, SD (không tự bịa bước dựng đường cao SA ⊥ (ABCD) vì không có chứng chỉ vuông góc!)
    expect(titles[1]).toMatch(/Dựng các cạnh bên SA, SB, SC, SD/u);
    expect(titles.some((t) => /đường cao SA/u.test(t))).toBe(false);
    expect(plan.steps[1].visibleIds).toContain("canh_ben_S_C");
    expect(plan.steps[1].visibleIds).not.toContain("khoi_S_ABCD");
    expect(plan.steps[1].visibleIds).not.toContain("M");

    // Bước 3: hoàn thiện khối chóp S.ABCD
    expect(titles[2]).toMatch(/Hoàn thiện hình chóp S\.ABCD/iu);
    expect(plan.steps[2].visibleIds).toContain("khoi_S_ABCD");
    expect(plan.steps[2].visibleIds).toContain("canh_ben_S_C");
    expect(plan.steps[2].visibleIds).not.toContain("M");

    // Bước 4: xác định trung điểm M của SC SAU KHI khối S.ABCD và cạnh SC đã tồn tại
    expect(titles[3]).toMatch(/Xác định trung điểm M của (SC|CS)/u);
    expect(plan.steps[3].prerequisiteIds).toEqual(
      expect.arrayContaining(["C", "S", "canh_ben_S_C", "khoi_S_ABCD"]),
    );
    expect(plan.steps[3].visibleIds).toContain("M");

    // Bước 5..6: mặt phẳng (MAB) -> giao tuyến và hoàn thiện thiết diện (không tiết lộ loại hình trên tiêu đề bước)
    expect(titles[4]).toMatch(/Dựng mặt phẳng cắt \(MAB\)/u);
    expect(titles[5]).toMatch(/Dựng các giao tuyến và hoàn thiện thiết diện/u);
    expect(titles[5]).not.toMatch(/hình thang/u);
  });

  it("Toàn bộ 11 mẫu & 10 họ hình học (lăng trụ, nón, trụ, mặt cầu, đường–mặt) đạt bất biến DAG tôpô + nhất quán toán học mà không bị ép vào khuôn hình chóp", () => {
    const auditScenes = loadRepoFixtureMap(
      "docs/evaluation/geometry/runs/geometric-visual-correctness-framing/demos/audit_scenes.json",
    );
    const sectionScenes = loadRepoFixtureMap(
      "docs/evaluation/geometry/runs/goal-directed-section-planning/visual/scenes.json",
    );
    const allCases: [string, Scene3D][] = [
      ...GEOMETRY_SAMPLES.map((s): [string, Scene3D] => [
        s.id,
        structuredClone((s.envelope as unknown as { scene3d: Scene3D }).scene3d),
      ]),
      ["family01_triangular_pyramid", structuredClone(auditScenes["family01_triangular_pyramid"])],
      ["family02_quadrilateral_pyramid", structuredClone(auditScenes["family02_quadrilateral_pyramid"])],
      ["family04_derived_sub_pyramid", structuredClone(auditScenes["family04_derived_sub_pyramid"])],
      ["family05_prism", structuredClone(auditScenes["family05_prism"])],
      ["family08_unnamed_section_vertices", structuredClone(auditScenes["family08_unnamed_section_vertices"])],
      ["family10_cone_frustum_cut", structuredClone(auditScenes["family10_cone_frustum_cut"])],
      ["family11_sphere_plane_cut", structuredClone(auditScenes["family11_sphere_plane_cut"])],
      ["family12_cylinder_ellipse_section", structuredClone(auditScenes["family12_cylinder_ellipse_section"])],
      ["section-MAB-trapezoid", structuredClone(sectionScenes["section-MAB-trapezoid"])],
      ["aux-foot-S-to-BD", structuredClone(sectionScenes["aux-foot-S-to-BD"])],
    ];

    for (const [cid, raw] of allCases) {
      const consistency = verifySceneMathematicalConsistency(raw);
      expect(consistency.valid, `[${cid}] ${JSON.stringify(consistency.contradictions)}`).toBe(true);

      const plan = buildPedagogicalConstructionPlan(withSubEntities(raw));
      expect(plan.steps.length, `[${cid}] không có bước sư phạm`).toBeGreaterThan(0);
      expect(plan.steps[plan.steps.length - 1].anchor).toBe(stepCount(plan.scene) - 1);

      const seen = new Set<string>(plan.scene.free_objects);
      for (const st of plan.steps) {
        expect(st.targetIds.length, `[${cid}] bước ${st.index} rỗng targetIds`).toBeGreaterThan(0);
        expect(st.operation.length, `[${cid}] bước ${st.index} rỗng operation`).toBeGreaterThan(0);
        expect(st.premise.length, `[${cid}] bước ${st.index} rỗng premise`).toBeGreaterThan(0);
        for (const pre of st.prerequisiteIds) {
          expect(seen.has(pre), `[${cid}] bước ${st.index} (${st.title}) thiếu tiên quyết ${pre}`).toBe(true);
        }
        for (const vId of st.visibleIds) seen.add(vId);
        for (const tId of st.targetIds) seen.add(tId);
      }
    }

    // Các khối tròn xoay và lăng trụ giữ đúng bản chất họ hình của chúng (không bị chèn ngôn ngữ hình chóp)
    const spherePlan = buildPedagogicalConstructionPlan(loadSampleScene("cau-cat-mat-phang"));
    expect(spherePlan.steps[0].title).toMatch(/mặt cầu/iu);
    expect(spherePlan.steps.some((s) => /hình chóp/iu.test(s.title))).toBe(false);

    const cylPlan = buildPedagogicalConstructionPlan(loadSampleScene("tru-thiet-dien-tron"));
    expect(cylPlan.steps[0].title).toMatch(/hình trụ/iu);
    expect(cylPlan.steps.some((s) => /hình chóp/iu.test(s.title))).toBe(false);

    const conePlan = buildPedagogicalConstructionPlan(loadSampleScene("non-thiet-dien-truc"));
    expect(conePlan.steps[0].title).toMatch(/hình nón/iu);
    expect(conePlan.steps.some((s) => /hình chóp/iu.test(s.title))).toBe(false);

    const prismPlan = buildPedagogicalConstructionPlan(structuredClone(auditScenes["family05_prism"]));
    expect(prismPlan.steps.some((s) => /lăng trụ/iu.test(s.title))).toBe(true);
    expect(prismPlan.steps.some((s) => /hình chóp/iu.test(s.title))).toBe(false);

    // Cảnh thuần đường thẳng & mặt phẳng độc lập + giao tuyến (không có khối chóp / lăng trụ / tròn xoay)
    const pureLinePlaneScene: Scene3D = {
      free_objects: ["A", "B", "C", "D", "E"],
      diagnostics: [],
      objects: [
        { id: "A", type: "point3", label: "Điểm A", notation: "A", origin: "free", producer: "declare_point", render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
        { id: "B", type: "point3", label: "Điểm B", notation: "B", origin: "free", producer: "declare_point", render: "point_marker", depends: [], xyz: ["2", "0", "0"] },
        { id: "C", type: "point3", label: "Điểm C", notation: "C", origin: "free", producer: "declare_point", render: "point_marker", depends: [], xyz: ["0", "2", "0"] },
        { id: "D", type: "point3", label: "Điểm D", notation: "D", origin: "free", producer: "declare_point", render: "point_marker", depends: [], xyz: ["0", "0", "2"] },
        { id: "E", type: "point3", label: "Điểm E", notation: "E", origin: "free", producer: "declare_point", render: "point_marker", depends: [], xyz: ["2", "2", "2"] },
        { id: "mp_ABC", type: "plane3", label: "Mặt phẳng (ABC)", notation: "(ABC)", origin: "derived", producer: "construct_plane.from_three_points", render: "surface", depends: ["A", "B", "C"], point: ["0", "0", "0"], normal: ["0", "0", "1"] },
        { id: "mp_ADE", type: "plane3", label: "Mặt phẳng (ADE)", notation: "(ADE)", origin: "derived", producer: "construct_plane.from_three_points", render: "surface", depends: ["A", "D", "E"], point: ["0", "0", "0"], normal: ["1", "-1", "0"] },
        { id: "giao_tuyen", type: "line3", label: "Giao tuyến Δ", notation: "Δ", role: "Giao tuyến của (ABC) và (ADE)", origin: "derived", producer: "construct_line.intersect_planes", render: "line", depends: ["mp_ABC", "mp_ADE"], point: ["0", "0", "0"], direction: ["1", "1", "0"], formation_roles: ["CONSTRUCT_INTERSECTION"] },
      ],
      events: [
        { step_index: 0, action: "INIT", object: null, depends: [], explanation: "Khởi tạo không gian." },
        { step_index: 1, action: "CREATE", object: "mp_ABC", depends: ["A", "B", "C"], explanation: "Dựng mặt phẳng (ABC)." },
        { step_index: 2, action: "CREATE", object: "mp_ADE", depends: ["A", "D", "E"], explanation: "Dựng mặt phẳng (ADE)." },
        { step_index: 3, action: "CREATE", object: "giao_tuyen", depends: ["mp_ABC", "mp_ADE"], explanation: "Dựng giao tuyến của (ABC) và (ADE)." },
      ],
    };
    expect(verifySceneMathematicalConsistency(pureLinePlaneScene).valid).toBe(true);
    const pureLinePlanePlan = buildPedagogicalConstructionPlan(pureLinePlaneScene);
    expect(pureLinePlanePlan.steps.length).toBe(3);
    expect(pureLinePlanePlan.steps.some((s) => /hình chóp|lăng trụ/iu.test(s.title))).toBe(false);
    expect(pureLinePlanePlan.steps[2].epistemicCategory).toBe("derived");
    expect(pureLinePlanePlan.steps[2].prerequisiteIds).toEqual(expect.arrayContaining(["mp_ABC", "mp_ADE"]));
  });
});

describe("§4 Case 3, §5 & §8 — Phân biệt hình thang vs hình thang vuông theo tiền đề & kiểm thử nhiễu bảo toàn / vô hiệu hóa giả thiết", () => {
  it("Phân biệt 3 cấu hình thiết diện qua (MAB): (1) chỉ đáy hình vuông, (2) đáy hình vuông + SA ⊥ (ABCD), (3) hình chóp xiên", () => {
    const sectionScenes = loadRepoFixtureMap(
      "docs/evaluation/geometry/runs/goal-directed-section-planning/visual/scenes.json",
    );

    // Cấu hình (1): Chỉ cho đáy ABCD hình vuông, M trung điểm SC, KHÔNG có chứng chỉ SA ⊥ (ABCD)
    // dù tọa độ thực hiện ngẫu nhiên đặt S = (0, 0, 1) thẳng trên A(0, 0, 0)!
    const noPerpScene = structuredClone(sectionScenes["section-MAB-trapezoid"]);
    const noPerpSec = noPerpScene.objects.find((o) => o.type === "section")!;
    const noPerpBasis = deriveExactPolygonMathBasis(noPerpScene, noPerpSec)!;
    expect(noPerpBasis.coordinateShape).toBe("hình thang vuông");
    expect(noPerpBasis.shape).toBe("hình thang");
    expect(noPerpBasis.epistemicLevel).toBe("DERIVED");
    expect(noPerpBasis.coordinateOnlyFacts.length).toBeGreaterThan(0);
    expect(noPerpBasis.undeterminedAspects.join(" ")).toMatch(/chưa đủ giả thiết.*vuông góc.*kết luận góc vuông/u);
    expect(noPerpBasis.diagnostics).toMatchObject({
      edgeCount: 4,
      boundaryConnected: true,
      coplanar: true,
      nonDegenerate: true,
    });
    expect(noPerpBasis.diagnostics.faceIncidences.length).toBe(4);

    // Cấu hình (2): Bổ sung giả thiết được chứng nhận đáy hình vuông ABCD + SA ⊥ (ABCD) (`perpendicular_witness` hợp lệ trên `canh_ben_S_A`)
    // trên CÙNG tọa độ => chứng minh hợp lệ là `hình thang vuông` và tự tách bước dựng đường cao SA ⊥ (ABCD)!
    const withPerpScene = structuredClone(sectionScenes["section-MAB-trapezoid"]);
    withPerpScene.objects.find((o) => o.id === "day_ABCD")!.label = "Đáy ABCD là hình vuông";
    const saEdge = withPerpScene.objects.find((o) => o.id === "canh_ben_S_A")!;
    saEdge.perpendicular_witness = {
      foot: ["0", "0", "0"],
      foot_id: "A",
      from: "S",
      on: "day_ABCD",
      relation: "line_perp_plane",
      plane_directions: [
        ["1", "0", "0"],
        ["0", "1", "0"],
      ],
      marker: {
        u: ["1", "0", "0"],
        v: ["0", "0", "1"],
      },
    };
    expect(verifySceneMathematicalConsistency(withPerpScene).valid).toBe(true);
    const withPerpPlan = buildPedagogicalConstructionPlan(withSubEntities(withPerpScene));
    expect(withPerpPlan.steps.length).toBe(7);
    expect(withPerpPlan.steps[1].title).toMatch(/Dựng đường cao SA ⊥ \(ABCD\) tại A/u);
    expect(withPerpPlan.steps[2].title).toMatch(/Dựng các cạnh bên SB, SC, SD/u);
    expect(withPerpPlan.steps[3].title).toMatch(/Hoàn thiện hình chóp S\.ABCD/iu);
    expect(withPerpPlan.steps[4].title).toMatch(/Xác định trung điểm M của (SC|CS)/u);
    expect(withPerpPlan.steps[6].title).toMatch(/Dựng các giao tuyến và hoàn thiện thiết diện/u);
    expect(withPerpPlan.steps[6].title).not.toMatch(/hình thang vuông/u);

    const withPerpSec = withPerpPlan.scene.objects.find((o) => o.type === "section")!;
    const withPerpBasis = deriveExactPolygonMathBasis(withPerpPlan.scene, withPerpSec)!;
    expect(withPerpBasis.shape).toBe("hình thang vuông");
    expect(withPerpBasis.epistemicLevel).toBe("DERIVED");
    expect(withPerpBasis.undeterminedAspects).toEqual([]);
    expect(withPerpBasis.supportingPremises.join(" ")).toContain("SA ⊥ (ABCD)");

    // Cấu hình (3): Hình chóp xiên S = (1/3, 1/4, 2) trên cùng đáy hình vuông ABCD, M trung điểm SC
    // => M = (2/3, 5/8, 1), mặt phẳng (MAB) đi qua A(0,0,0), B(1,0,0), M(2/3, 5/8, 1) có pháp tuyến (0, -8, 5),
    // cắt SD tại N = (1/6, 5/8, 1) (trung điểm SD) => thiết diện là `hình thang` (không vuông)
    const obliqueScene = structuredClone(sectionScenes["section-MAB-trapezoid"]);
    const setObliquePt = (id: string, xyz: ExactVec3) => {
      const o = obliqueScene.objects.find((x) => x.id === id)!;
      o.xyz = xyz;
      if (o.polygon) o.polygon = [xyz];
    };
    setObliquePt("S", ["1/3", "1/4", "2"]);
    setObliquePt("M", ["2/3", "5/8", "1"]);
    const sol = obliqueScene.objects.find((x) => x.id === "khoi_S_ABCD")!;
    sol.vertices = [
      ["1/3", "1/4", "2"],
      ["0", "0", "0"],
      ["1", "0", "0"],
      ["1", "1", "0"],
      ["0", "1", "0"],
    ];
    for (const [eid, bPt] of [
      ["canh_ben_S_A", ["0", "0", "0"]],
      ["canh_ben_S_B", ["1", "0", "0"]],
      ["canh_ben_S_C", ["1", "1", "0"]],
      ["canh_ben_S_D", ["0", "1", "0"]],
    ] as [string, ExactVec3][]) {
      const seg = obliqueScene.objects.find((x) => x.id === eid)!;
      seg.point_a = ["1/3", "1/4", "2"];
      seg.point_b = bPt;
      seg.endpoints = [["1/3", "1/4", "2"], bPt];
    }
    const mpObl = obliqueScene.objects.find((x) => x.id === "mp_td_f6")!;
    mpObl.point = ["0", "0", "0"];
    mpObl.normal = ["0", "-8", "5"];
    const secObl = obliqueScene.objects.find((x) => x.id === "td_f6")!;
    const N_obl: ExactVec3 = ["1/6", "5/8", "1"];
    const M_obl: ExactVec3 = ["2/3", "5/8", "1"];
    secObl.polygon = [["0", "0", "0"], ["1", "0", "0"], M_obl, N_obl];
    secObl.steps = [
      { face_index: 0, a: ["0", "0", "0"], b: ["1", "0", "0"] },
      { face_index: 2, a: ["1", "0", "0"], b: M_obl },
      { face_index: 3, a: M_obl, b: N_obl },
      { face_index: 4, a: N_obl, b: ["0", "0", "0"] },
    ];
    expect(verifySceneMathematicalConsistency(obliqueScene).valid).toBe(true);
    const oblBasis = deriveExactPolygonMathBasis(obliqueScene, secObl)!;
    expect(oblBasis.coordinateShape).toBe("hình thang");
    expect(oblBasis.shape).toBe("hình thang");
    expect(oblBasis.undeterminedAspects).toEqual([]);
  });

  it("Biến đổi tọa độ bảo toàn giả thiết (phép trượt tuyến tính kèm metric Gram SPD) giữ nguyên kết luận hình vuông; đổi giả thiết làm kết luận thay đổi", () => {
    // Phép biến đổi tuyến tính khả nghịch x' = (x + z, y, z) với metric Gram kéo lùi G' = [[1, 0, -1], [0, 1, 0], [-1, 0, 2]]:
    // giữ nguyên 100% độ dài, góc vuông và giả thiết SA ⊥ (ABCD), dù tọa độ số S' = (4, 0, 4) bị nghiêng trong R^3 chuẩn!
    const sheared = loadSampleScene("thiet-dien-chop");
    const shearPt = (v: ExactVec3): ExactVec3 => {
      const parseF = (s: string): [bigint, bigint] => {
        if (s.includes("/")) {
          const [a, b] = s.split("/");
          return [BigInt(a), BigInt(b)];
        }
        return [BigInt(s), 1n];
      };
      const gcd = (a: bigint, b: bigint): bigint => {
        let x = a < 0n ? -a : a;
        let y = b < 0n ? -b : b;
        while (y !== 0n) [x, y] = [y, x % y];
        return x === 0n ? 1n : x;
      };
      const [xn, xd] = parseF(v[0]);
      const [zn, zd] = parseF(v[2]);
      const num = xn * zd + zn * xd;
      const den = xd * zd;
      const g = gcd(num, den);
      const xNew = den / g === 1n ? (num / g).toString() : `${(num / g).toString()}/${(den / g).toString()}`;
      return [xNew, v[1], v[2]];
    };

    sheared.chart_metric = [
      ["1", "0", "-1"],
      ["0", "1", "0"],
      ["-1", "0", "2"],
    ];
    for (const o of sheared.objects) {
      if (o.xyz) o.xyz = shearPt(o.xyz);
      if (o.point_a) o.point_a = shearPt(o.point_a);
      if (o.point_b) o.point_b = shearPt(o.point_b);
      if (o.endpoints) o.endpoints = [shearPt(o.endpoints[0]), shearPt(o.endpoints[1])];
      if (o.vertices) o.vertices = o.vertices.map(shearPt);
      if (o.polygon) o.polygon = o.polygon.map(shearPt);
      if (o.steps) o.steps = o.steps.map((st) => ({ ...st, a: shearPt(st.a), b: shearPt(st.b) }));
      if (o.id === "mp") {
        o.point = ["2", "0", "2"];
        o.normal = ["0", "0", "1"];
      }
      if (o.id === "sd") {
        o.point = ["4", "0", "4"];
        o.direction = ["-4", "2", "-4"];
      }
      if (o.perpendicular_witness?.marker) {
        o.perpendicular_witness = {
          ...o.perpendicular_witness,
          foot: shearPt(o.perpendicular_witness.foot),
          marker: {
            u: shearPt(o.perpendicular_witness.marker.u),
            v: shearPt(o.perpendicular_witness.marker.v),
          },
          ...(o.perpendicular_witness.plane_directions
            ? { plane_directions: o.perpendicular_witness.plane_directions.map(shearPt) }
            : {}),
        };
      }
    }

    sheared.objects.find((o) => o.id === "day_ABCD")!.label = "Đáy ABCD là hình vuông";
    const shearCheck = verifySceneMathematicalConsistency(sheared);
    expect(shearCheck.valid, JSON.stringify(shearCheck.contradictions)).toBe(true);

    const shearedSec = sheared.objects.find((o) => o.id === "thiet_dien")!;
    const shearedBasis = deriveExactPolygonMathBasis(sheared, shearedSec)!;
    expect(shearedBasis.shape).toBe("hình vuông");
    expect(shearedBasis.epistemicLevel).toBe("DERIVED");

    // (a) Với mặt cắt (MNP) ∥ (ABCD), kể cả khi bỏ giả thiết SA ⊥ (ABCD), phép vị tự tâm S tỉ số 1/2 VẪN bảo toàn hình vuông từ đáy ABCD:
    const obliqueHomothetic = structuredClone(sheared);
    for (const o of obliqueHomothetic.objects) {
      delete o.perpendicular_witness;
      o.formation_roles = (o.formation_roles ?? []).filter((r) => r !== "CONSTRUCT_HEIGHT");
    }
    const obliqueHomoBasis = deriveExactPolygonMathBasis(
      obliqueHomothetic,
      obliqueHomothetic.objects.find((o) => o.id === "thiet_dien")!,
    )!;
    expect(obliqueHomoBasis.shape).toBe("hình vuông");

    // (b) Ngược lại, thay đổi giả thiết mặt đáy từ hình vuông (AB ⊥ AD) thành hình thoi góc 60° (G'_{01} = 1/2, AB = AD = 2 nhưng không vuông góc)
    // => kết luận thiết diện MNPQ lập tức đổi từ "hình vuông" sang "hình thoi" (không còn góc vuông)!
    const rhombusBaseScene = structuredClone(sheared);
    rhombusBaseScene.objects.find((o) => o.id === "day_ABCD")!.label = "Đáy ABCD là hình thoi";
    rhombusBaseScene.chart_metric = [
      ["1", "1/2", "-1"],
      ["1/2", "1", "-1/2"],
      ["-1", "-1/2", "2"],
    ];
    expect(verifySceneMathematicalConsistency(rhombusBaseScene).valid).toBe(true);
    const rhombusSec = rhombusBaseScene.objects.find((o) => o.id === "thiet_dien")!;
    const rhombusBasis = deriveExactPolygonMathBasis(rhombusBaseScene, rhombusSec)!;
    expect(rhombusBasis.shape).toBe("hình thoi");
    expect(rhombusBasis.summary).not.toContain("hình vuông");
  });
});

describe("§6 — Nhấn mạnh đối tượng độc lập với bảng màu ngữ nghĩa (Default / Hover / Selected-Active)", () => {
  it("Bước 9 xác định Q và khi chọn Q: cạnh khối SD giữ họ màu slate-navy #1E293B (|Δhue| < 2°), tuyệt đối không đổi sang xanh ngọc #0F766E của đường cao", () => {
    const plan = buildPedagogicalConstructionPlan(withSubEntities(loadSampleScene("thiet-dien-chop")));
    const scene = plan.scene;
    const step8Anchor = plan.steps[8].anchor;
    const present = scene.objects.filter((o) => entitiesPresentAt(scene, step8Anchor, objectsAt).has(o.id));
    const byId = new Map(scene.objects.map((o) => [o.id, o]));

    const isSemanticDefaultEdge = (id: string) => {
      const src = byId.get(id);
      if (!src || (src.type !== "segment3" && src.type !== "line3")) return false;
      const roles = src.formation_roles ?? [];
      return Boolean(src.perpendicular_witness || src.annotation?.witness) || roles.includes("CONSTRUCT_HEIGHT");
    };
    const { ca: defaultEdgeColors } = toSangCanhChuan(
      present,
      isSemanticDefaultEdge,
      (id) => classifySceneObjectSemantics(scene, byId.get(id)!, step8Anchor).strokeColor,
    );

    // Đường cao SA mang màu #0F766E, trong khi cạnh bên SD không có trong `defaultEdgeColors` nên giữ màu cạnh khối #1E293B
    expect(defaultEdgeColors.get("chop::edge:A-S")).toBe(PHONG_CACH_SCENE3D.colors.line);
    expect(defaultEdgeColors.has("chop::edge:D-S")).toBe(false);

    // Tại Bước 8 (khi `sd` vừa được dùng để cắt `(MNP)` tại `Q`) và khi người học click chọn `Q`:
    // `canonicalHighlights` nhấn mạnh `chop::edge:D-S` bằng họ màu gốc của chính cạnh đó (`modulateSemanticColor(canh, "selected")`),
    // không bao giờ nhuộm xanh ngọc `#0F766E`!
    const { ca: step8Highlights } = toSangCanhChuan(
      present,
      (id) => id === "sd",
      (id, edgeId) => {
        const baseHex = edgeId ? defaultEdgeColors.get(edgeId) : undefined;
        if (baseHex !== undefined) return modulateSemanticColor(baseHex, "selected");
        if (isSemanticDefaultEdge(id)) return classifySceneObjectSemantics(scene, byId.get(id)!, step8Anchor, id).strokeColor;
        return modulateSemanticColor(PHONG_CACH_SCENE3D.colors.canh, "selected");
      },
    );

    const sdHighlightedHex = step8Highlights.get("chop::edge:D-S")!;
    expect(sdHighlightedHex).toBeDefined();
    expect(hueDeltaDegrees(sdHighlightedHex, PHONG_CACH_SCENE3D.colors.canh)).toBeLessThan(2.0);
    expect(hueDeltaDegrees(sdHighlightedHex, PHONG_CACH_SCENE3D.colors.line)).toBeGreaterThan(30.0);

    // Kiểm tra trực tiếp trên đối tượng 3D của khối `chop` dựng tại Bước 8 và khôi phục về mặc định khi bỏ chọn / sang bước sau
    const chopObj = present.find((o) => o.id === "chop")!;
    const builtHighlighted = buildObject3D(
      chopObj,
      false,
      undefined,
      diemHuuHan(present),
      undefined,
      step8Highlights,
      new Map(),
      false,
      "primary",
      true,
      true,
      false,
      scene,
      defaultEdgeColors,
      new Set(),
    )!;
    let sdEdgeColorActive: number | undefined;
    let saEdgeColorDefault: number | undefined;
    builtHighlighted.traverse((node) => {
      const ud = node.userData as { visualOwnerId?: string; highlightColor?: number; edgeColor?: number } | undefined;
      if (ud?.visualOwnerId === "chop::edge:D-S") sdEdgeColorActive = ud.highlightColor;
      if (ud?.visualOwnerId === "chop::edge:A-S") saEdgeColorDefault = ud.edgeColor;
    });
    expect(sdEdgeColorActive).toBeDefined();
    expect(saEdgeColorDefault).toBe(PHONG_CACH_SCENE3D.colors.line);
    expect(hueDeltaDegrees(sdEdgeColorActive!, PHONG_CACH_SCENE3D.colors.canh)).toBeLessThan(2.0);

    // Phân biệt 3 trạng thái Default / Hover / Selected và khôi phục gốc khi unhover / deselect cho mọi vai trò ngữ nghĩa
    const roleChecks: [string, number][] = [
      ["chop", PHONG_CACH_SCENE3D.colors.canh],
      ["chieu_cao_SA", PHONG_CACH_SCENE3D.colors.line],
      ["mp", PHONG_CACH_SCENE3D.colors.planeOutline],
      ["thiet_dien", PHONG_CACH_SCENE3D.colors.sectionOutline],
      ["canh_ben_S_B", PHONG_CACH_SCENE3D.colors.canh],
    ];
    const finalAnchor = plan.steps[9].anchor;
    for (const [objId, expectedBaseHex] of roleChecks) {
      const obj = byId.get(objId);
      if (!obj) continue;
      const stDefault = classifySceneObjectSemantics(scene, obj, finalAnchor, null, null);
      const stHover = classifySceneObjectSemantics(scene, obj, finalAnchor, null, objId);
      const stSelected = classifySceneObjectSemantics(scene, obj, finalAnchor, objId, null);
      const stRestored = classifySceneObjectSemantics(scene, obj, finalAnchor, null, null);

      expect(stDefault.strokeColor).toBe(expectedBaseHex);
      expect(stHover.strokeColor).not.toBe(stDefault.strokeColor);
      expect(stSelected.strokeColor).not.toBe(stHover.strokeColor);
      expect(hueDeltaDegrees(stHover.strokeColor, expectedBaseHex)).toBeLessThan(2.0);
      expect(hueDeltaDegrees(stSelected.strokeColor, expectedBaseHex)).toBeLessThan(2.0);
      expect(stRestored).toEqual(stDefault);
    }

    // Bề dày nét tăng có phân cấp rõ ràng: Default < Hover < Selected
    expect(PHONG_CACH_SCENE3D.fatPx.edge).toBeLessThan(PHONG_CACH_SCENE3D.fatPx.hoverEdge);
    expect(PHONG_CACH_SCENE3D.fatPx.hoverEdge).toBeLessThan(PHONG_CACH_SCENE3D.fatPx.selectedEdge);
    expect(PHONG_CACH_SCENE3D.fatPx.section).toBeLessThan(PHONG_CACH_SCENE3D.fatPx.hoverSection);
    expect(PHONG_CACH_SCENE3D.fatPx.hoverSection).toBeLessThan(PHONG_CACH_SCENE3D.fatPx.selectedSection);
  });

  it("AxoWorkspaceV62 kiểm chứng đại số chính xác trên cảnh khung Q^3 gốc trước khi nhúng Cholesky veKhongGian (không báo lỗi giả do làm tròn 1e-9)", () => {
    const sectionScenes = loadRepoFixtureMap(
      "docs/evaluation/geometry/runs/goal-directed-section-planning/visual/scenes.json",
    );
    const mabRaw = structuredClone(sectionScenes["section-MAB-trapezoid"]);
    const html = renderToStaticMarkup(<AxoWorkspaceV62 scene={mabRaw} de="Cho hình chóp S.ABCD đáy hình vuông, M trung điểm SC." tieuDe="Thiết diện (MAB)" />);
    expect(html).not.toContain("data-math-contradiction");
    expect(html).toContain("là hình thang");
    expect(html).not.toContain("là hình thang vuông");
    expect(html).toContain("chưa đủ giả thiết");
  });
});
