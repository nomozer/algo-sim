import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import * as THREE from "three";
import advancedSamplesRaw from "../../../data/advanced-geometry-samples.json";
import { PUBLIC_GEOMETRY_SAMPLES } from "../../../data/geometry-samples";
import { diemHuuHan, objectsAt, type Scene3D } from "./scene3d-model";
import { PHONG_CACH_SCENE3D } from "./scene3d-roles";
import { diemVuaKhung, dungTrucOxyzSuPham, tinhTamXoayOnDinh } from "./scene3d-view";
import { veKhongGian } from "./scene3d-chart";
import { AxoWorkspaceV62 } from "../../../components/SimulationWorkspace";
import {
  buildPedagogicalConstructionPlan,
  classifySceneObjectSemantics,
  isExplicitOxyzCoordinateScene,
  resolveCertifiedRightAngleMarkers,
  resolveVerifiedAngleArcs,
} from "./scene3d-semantic-policy";

type AdvancedSampleEntry = {
  id: string;
  title?: string;
  problemText?: string;
  envelope: {
    title?: string;
    description?: string;
    scene3d: Scene3D;
  };
};

const ADVANCED_SAMPLES: AdvancedSampleEntry[] = Array.isArray(
  (advancedSamplesRaw as unknown as { samples?: AdvancedSampleEntry[] }).samples,
)
  ? (advancedSamplesRaw as unknown as { samples: AdvancedSampleEntry[] }).samples
  : (advancedSamplesRaw as unknown as AdvancedSampleEntry[]);

function sampleById(id: string): AdvancedSampleEntry {
  const found = ADVANCED_SAMPLES.find((s) => s.id === id);
  if (!found) throw new Error(`Missing sample: ${id}`);
  return found;
}

describe("Scene3D Standardization — Semantic Colors, Oxyz, Symbols, Steps & 7 General Test Cases", () => {
  it("B1: PHONG_CACH_SCENE3D.colors đồng bộ đúng bảng token DESIGN.md & matphang.html", () => {
    const c = PHONG_CACH_SCENE3D.colors as Record<string, number>;
    expect(c.line).toBe(0x0f766e); // Teal #0F766E (đường cao / quan hệ vuông góc)
    expect(c.studiedLine).toBe(0x2563eb); // Cobalt #2563EB (đường thẳng đang xét)
    expect(c.angleArc).toBe(0x2563eb); // Cobalt #2563EB (cung góc đang xét)
    expect(c.sectionOutline).toBe(0xc85a32); // Terracotta #C85A32 (thiết diện mục tiêu)
    expect(c.surface).toBe(0x6d28d9); // Violet #6D28D9 (mặt phẳng)
    expect(c.inscribed).toBe(0xd97706); // Amber #D97706 (đường tròn nội tiếp — matphang.html:1798)
    expect(c.circumscribedCircle).toBe(0x2563eb); // Cobalt #2563EB (đường tròn ngoại tiếp — matphang.html:1810, phân biệt đồng tâm với nội tiếp)
    expect(c.circumscribedSphere).toBe(0x0f766e); // Teal #0F766E (mặt cầu ngoại tiếp)
    expect(c.canh).toBe(0x1e293b); // Trung tính cấu trúc #1E293B
    expect(c.hiddenEdge).toBe(0x64748b); // Nét đứt khuất #64748B
  });

  it("B2 & B4: Phân biệt cạnh khối trung tính, đường cao Teal, đường thẳng xét Cobalt và mặt phẳng chắn Oxyz Violet", () => {
    // 1. Cạnh bên lăng trụ đứng AA′, BB′, CC′ giữ màu cấu trúc trung tính #1E293B (không tô nhầm Teal)
    const prismScene = buildPedagogicalConstructionPlan(
      veKhongGian(sampleById("lang-tru-tam-giac-thiet-dien").envelope.scene3d),
    ).scene;
    for (const edgeId of ["canh_ben_A_A_prime", "canh_ben_B_B_prime", "canh_ben_C_C_prime"]) {
      const edgeObj = prismScene.objects.find((o) => o.id === edgeId);
      expect(edgeObj).toBeDefined();
      const sem = classifySceneObjectSemantics(prismScene, edgeObj!);
      expect(sem.strokeColor).toBe(0x1e293b);
    }

    // 2. Cạnh chóp đồng thời là đường cao SA -> Teal #0F766E; thiết diện -> Terracotta #C85A32
    const pyrScene = buildPedagogicalConstructionPlan(
      veKhongGian(sampleById("chop-thiet-dien-ba-diem").envelope.scene3d),
    ).scene;
    const saObj = pyrScene.objects.find((o) => o.id === "chieu_cao_SA")!;
    const sbObj = pyrScene.objects.find((o) => o.id === "canh_ben_S_B")!;
    const secObj = pyrScene.objects.find((o) => o.id === "thiet_dien")!;
    expect(classifySceneObjectSemantics(pyrScene, saObj).strokeColor).toBe(0x0f766e);
    expect(classifySceneObjectSemantics(pyrScene, sbObj).strokeColor).toBe(0x1e293b);
    expect(classifySceneObjectSemantics(pyrScene, secObj).strokeColor).toBe(0xc85a32);

    // 3. Hai đường chéo nhau SC và BD -> Cobalt #2563EB; đoạn vuông góc chung PQ -> Teal #0F766E
    const skewScene = buildPedagogicalConstructionPlan(
      veKhongGian(sampleById("khoang-cach-hai-duong-cheo-nhau").envelope.scene3d),
    ).scene;
    const scLine = skewScene.objects.find((o) => o.id === "sc")!;
    const bdSeg = skewScene.objects.find((o) => o.id === "doan_BD")!;
    const pqSeg = skewScene.objects.find((o) => o.id === "doan_PQ")!;
    expect(classifySceneObjectSemantics(skewScene, scLine).strokeColor).toBe(0x2563eb);
    expect(classifySceneObjectSemantics(skewScene, bdSeg).strokeColor).toBe(0x2563eb);
    expect(classifySceneObjectSemantics(skewScene, pqSeg).strokeColor).toBe(0x0f766e);

    // 4. Trong Oxyz (không có khối cắt), tam giác chắn trục tam_giac_ABC biểu diễn mặt phẳng (P) -> Violet #6D28D9 (không phải Terracotta thiết diện!)
    const oxyzScene = buildPedagogicalConstructionPlan(
      veKhongGian(sampleById("oxyz-giao-diem-duong-mat").envelope.scene3d),
    ).scene;
    const triABC = oxyzScene.objects.find((o) => o.id === "tam_giac_ABC")!;
    const lineD = oxyzScene.objects.find((o) => o.id === "duong_d")!;
    const segEH = oxyzScene.objects.find((o) => o.id === "doan_EH")!;
    const segOM = oxyzScene.objects.find((o) => o.id === "doan_OM")!;
    expect(classifySceneObjectSemantics(oxyzScene, triABC).strokeColor).toBe(0x6d28d9);
    expect(classifySceneObjectSemantics(oxyzScene, lineD).strokeColor).toBe(0x2563eb);
    expect(classifySceneObjectSemantics(oxyzScene, segEH).strokeColor).toBe(0x0f766e);
    expect(classifySceneObjectSemantics(oxyzScene, segOM).strokeColor).toBe(0x2563eb);
  });

  it("B3: Ký hiệu vuông góc ⊥ và cung góc 3D được chứng nhận hình học chính xác trên các bài tiêu biểu", () => {
    // Góc nhị diện: có dấu vuông góc tại A và tại H (AH ⊥ BC, SH ⊥ BC) + cung góc phẳng nhị diện ∠SHA tại H
    const dihPlan = buildPedagogicalConstructionPlan(
      veKhongGian(sampleById("goc-nhi-dien-hai-mat-phang").envelope.scene3d),
    );
    const dihFinalObjs = objectsAt(dihPlan.scene, dihPlan.scene.events.length - 1);
    const dihRightMarkers = resolveCertifiedRightAngleMarkers(dihPlan.scene, dihFinalObjs);
    expect(dihRightMarkers.some((m) => m.footId === "H")).toBe(true);
    const dihArcs = resolveVerifiedAngleArcs(dihPlan.scene, dihFinalObjs);
    expect(dihArcs.length).toBeGreaterThanOrEqual(1);
    expect(dihArcs.some((a) => a.vertexId === "H" && a.color === 0x2563eb)).toBe(true);

    // Khoảng cách hai đường chéo nhau: dấu vuông góc tại P (trên SC) và tại Q (trên BD)
    const skewPlan = buildPedagogicalConstructionPlan(
      veKhongGian(sampleById("khoang-cach-hai-duong-cheo-nhau").envelope.scene3d),
    );
    const skewFinalObjs = objectsAt(skewPlan.scene, skewPlan.scene.events.length - 1);
    const skewMarkers = resolveCertifiedRightAngleMarkers(skewPlan.scene, skewFinalObjs);
    expect(skewMarkers.some((m) => m.footId === "P")).toBe(true);
    expect(skewMarkers.some((m) => m.footId === "Q")).toBe(true);

    // Oxyz giao điểm đường - mặt: dấu vuông góc tại H (EH ⊥ HM trên (P))
    const oxyzPlan = buildPedagogicalConstructionPlan(
      veKhongGian(sampleById("oxyz-giao-diem-duong-mat").envelope.scene3d),
    );
    const oxyzFinalObjs = objectsAt(oxyzPlan.scene, oxyzPlan.scene.events.length - 1);
    const oxyzMarkers = resolveCertifiedRightAngleMarkers(oxyzPlan.scene, oxyzFinalObjs);
    expect(oxyzMarkers.some((m) => m.footId === "H")).toBe(true);

    // Mặt phẳng tiếp xúc mặt cầu: dấu vuông góc tại tiếp điểm A dọc theo đoạn AB hoặc AC nằm trong mặt tiếp diện
    const tanPlan = buildPedagogicalConstructionPlan(
      veKhongGian(sampleById("mat-phang-tiep-xuc-mat-cau").envelope.scene3d),
    );
    const tanFinalObjs = objectsAt(tanPlan.scene, tanPlan.scene.events.length - 1);
    const tanMarkers = resolveCertifiedRightAngleMarkers(tanPlan.scene, tanFinalObjs);
    expect(tanMarkers.some((m) => m.footId === "A")).toBe(true);
  });

  it("C1–C3: Nhận diện bài toán Oxyz chính xác, tự bật hệ trục Ox/Oy/Oz cho bài tọa độ và tắt cho bài tổng hợp", () => {
    const oxyzIds = PUBLIC_GEOMETRY_SAMPLES.filter((s) =>
      isExplicitOxyzCoordinateScene((s.envelope as unknown as { scene3d: Scene3D }).scene3d),
    ).map((s) => s.id);
    expect(oxyzIds.sort()).toEqual([
      "mat-cau-cat-mat-phang",
      "mat-phang-tiep-xuc-mat-cau",
      "oxyz-giao-diem-duong-mat",
    ]);

    // SimulationWorkspace SSR: bật chấm trục #p-dot-axes.is-on cho bài Oxyz và tắt cho bài tổng hợp
    const oxyzSample = sampleById("oxyz-giao-diem-duong-mat");
    const oxyzHtml = renderToString(
      <AxoWorkspaceV62
        scene={oxyzSample.envelope.scene3d}
        de={oxyzSample.problemText ?? ""}
        deSource="catalog"
        tieuDe={oxyzSample.title}
        initialDisplayPopOpen
      />,
    );
    expect(oxyzHtml).toMatch(/<span[^>]*class="[^"]*is-on[^"]*"[^>]*id="p-dot-axes"/);

    const synthSample = sampleById("chop-thiet-dien-ba-diem");
    const synthHtml = renderToString(
      <AxoWorkspaceV62
        scene={synthSample.envelope.scene3d}
        de={synthSample.problemText ?? ""}
        deSource="catalog"
        tieuDe={synthSample.title}
        initialDisplayPopOpen
      />,
    );
    expect(synthHtml).not.toMatch(/<span[^>]*class="[^"]*is-on[^"]*"[^>]*id="p-dot-axes"/);

    // dungTrucOxyzSuPham tạo đủ 3 mũi tên dương Ox, Oy, Oz, nhãn x, y, z tách biệt và không làm đổi framing
    const anchorPts = [
      new THREE.Vector3(6, 0, 0),
      new THREE.Vector3(0, 6, 0),
      new THREE.Vector3(0, 0, 6),
    ];
    const axesGroup = dungTrucOxyzSuPham(anchorPts, { hasExplicitOriginLabel: false });
    const meshNames: string[] = [];
    const spriteNames: string[] = [];
    axesGroup.traverse((child) => {
      if (child.name) {
        if (child instanceof THREE.Mesh) meshNames.push(child.name);
        if (child instanceof THREE.Sprite) spriteNames.push(child.name);
      }
    });
    expect(meshNames.sort()).toEqual(["truc:Ox:mui", "truc:Oy:mui", "truc:Oz:mui"]);
    expect(spriteNames).toEqual(
      expect.arrayContaining(["truc:Ox:nhan", "truc:Oy:nhan", "truc:Oz:nhan", "truc:O:nhan"]),
    );

    const oxyzPlaced = veKhongGian(oxyzSample.envelope.scene3d);
    const finitePts = diemHuuHan(oxyzPlaced.objects);
    const rootWithoutAxes = new THREE.Group();
    const rootWithAxes = new THREE.Group();
    rootWithAxes.add(axesGroup);
    expect(diemVuaKhung(rootWithAxes, finitePts)).toEqual(diemVuaKhung(rootWithoutAxes, finitePts));
    const tam = tinhTamXoayOnDinh(oxyzPlaced.objects);
    expect(tam).not.toBeNull();
    expect(new THREE.Vector3(...tam!.tamXoay).distanceTo(new THREE.Vector3(2.3, 2.3, 2.65))).toBeLessThan(1.5);
  });

  it("D: Kiểm toán 11 bài THPT nâng cao — không còn bước thừa 'Xác định đường thẳng chứa cạnh' hay mặt phẳng trung trực gọi nhầm là 'mặt phẳng cắt'", () => {
    expect(ADVANCED_SAMPLES).toHaveLength(11);
    for (const sample of ADVANCED_SAMPLES) {
      const plan = buildPedagogicalConstructionPlan(veKhongGian(sample.envelope.scene3d));
      expect(plan.steps.length).toBeGreaterThanOrEqual(4);
      for (const st of plan.steps) {
        expect(st.title, `${sample.id} step ${st.index}`).not.toMatch(
          /^Xác định đường thẳng chứa cạnh\b/u,
        );
        expect(st.title, `${sample.id} step ${st.index}`).not.toMatch(
          /^Xác định cạnh .* trên khối đã dựng$/u,
        );
        expect(st.title, `${sample.id} step ${st.index}`).not.toContain(
          "của hình nón và qua I",
        );
        if (st.epistemicCategory === "derived") {
          expect(
            st.prerequisiteIds.length,
            `${sample.id} derived step '${st.title}' must have prerequisites`,
          ).toBeGreaterThan(0);
          expect(st.premise.trim().length).toBeGreaterThan(0);
        }
      }
    }

    // Lập phương thiết diện: không có bước thừa 'Dựng đoạn thẳng MN' sau khi đã khép kín (MNEPFQ)
    const cubePlan = buildPedagogicalConstructionPlan(
      veKhongGian(sampleById("lap-phuong-thiet-dien-bat-ky").envelope.scene3d),
    );
    expect(cubePlan.steps[cubePlan.steps.length - 1]?.title).not.toBe("Dựng đoạn thẳng MN");

    // Chóp mặt cầu ngoại tiếp: mặt phẳng (α), (β) là mặt phẳng trung trực, không gọi là 'mặt phẳng cắt'
    const circumPlan = buildPedagogicalConstructionPlan(
      veKhongGian(sampleById("chop-mat-cau-ngoai-tiep").envelope.scene3d),
    );
    for (const st of circumPlan.steps) {
      expect(st.title).not.toMatch(/Dựng mặt phẳng cắt \(\s*[αβγ]\s*\)/u);
      expect(st.title).not.toBe("Xác định trung điểm của AB");
      expect(st.title).not.toBe("Xác định trung điểm của AD");
    }
  });

  it("G (§9.1–7): Kiểm thử độc lập trên 7 trường hợp tổng quát ngoài thư viện mẫu", () => {
    // Case 1: Chóp có cạnh bên SB (không phải SA) đồng thời là đường cao
    const case1Scene = ({
      objects: [
        { id: "A", type: "point3", label: "Điểm A", notation: "A", origin: "free", render: "point_marker", xyz: ["3", "0", "0"] },
        { id: "B", type: "point3", label: "Điểm B", notation: "B", origin: "free", render: "point_marker", xyz: ["0", "0", "0"] },
        { id: "C", type: "point3", label: "Điểm C", notation: "C", origin: "free", render: "point_marker", xyz: ["0", "4", "0"] },
        { id: "S", type: "point3", label: "Điểm S", notation: "S", origin: "free", render: "point_marker", xyz: ["0", "0", "5"] },
        { id: "day_ABC", type: "polygon3", label: "Đáy ABC", notation: "ABC", origin: "derived", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_BASE"], depends: ["A", "B", "C"], render: "filled_polygon", vertices: [["3", "0", "0"], ["0", "0", "0"], ["0", "4", "0"]] },
        {
          id: "cao_SB",
          type: "segment3",
          label: "Đường cao SB",
          notation: "SB",
          origin: "derived",
          formation_roles: ["CONSTRUCT_HEIGHT", "CONSTRUCT_LATERAL_BOUNDARY"],
          depends: ["B", "S"],
          endpoint_ids: ["S", "B"],
          render: "segment",
          point_a: ["0", "0", "5"],
          point_b: ["0", "0", "0"],
          perpendicular_witness: {
            relation: "line_perpendicular_plane",
            status: "ENGINE_VERIFIED",
            from: "S",
            foot_id: "B",
            foot: ["0", "0", "0"],
            on: "day_ABC",
            can_present_as_proven: true,
            plane_directions: [["3", "0", "0"], ["0", "4", "0"]],
            marker: { u: ["3", "0", "0"], v: ["0", "0", "5"] },
          },
        },
        { id: "canh_SA", type: "segment3", label: "Cạnh SA", notation: "SA", origin: "derived", formation_roles: ["CONSTRUCT_LATERAL_BOUNDARY"], depends: ["A", "S"], endpoint_ids: ["S", "A"], render: "segment", point_a: ["0", "0", "5"], point_b: ["3", "0", "0"] },
        { id: "canh_SC", type: "segment3", label: "Cạnh SC", notation: "SC", origin: "derived", formation_roles: ["CONSTRUCT_LATERAL_BOUNDARY"], depends: ["C", "S"], endpoint_ids: ["S", "C"], render: "segment", point_a: ["0", "0", "5"], point_b: ["0", "4", "0"] },
        { id: "chop", type: "solid", label: "Hình chóp S.ABC", notation: "S.ABC", origin: "derived", formation_roles: ["CLOSE_SOLID"], depends: ["A", "B", "C", "S"], vertex_ids: ["A", "B", "C", "S"], vertices: [["3", "0", "0"], ["0", "0", "0"], ["0", "4", "0"], ["0", "0", "5"]], faces: [[0, 1, 2], [3, 0, 1], [3, 1, 2], [3, 2, 0]], render: "solid_mesh" },
      ],
      events: [
        { step_index: 0, action: "CREATE", object: "day_ABC", objects: ["A", "B", "C", "day_ABC"], depends: [] },
        { step_index: 1, action: "CREATE", object: "cao_SB", objects: ["S", "cao_SB"], depends: ["day_ABC"] },
        { step_index: 2, action: "CREATE", object: "canh_SA", objects: ["canh_SA", "canh_SC"], depends: ["S", "A", "C"] },
        { step_index: 3, action: "CREATE", object: "chop", objects: ["chop"], depends: ["day_ABC", "cao_SB", "canh_SA", "canh_SC"] },
      ],
    }) as unknown as Scene3D;
    expect(isExplicitOxyzCoordinateScene(case1Scene)).toBe(false);
    expect(classifySceneObjectSemantics(case1Scene, case1Scene.objects.find((o) => o.id === "cao_SB")!).strokeColor).toBe(0x0f766e);
    expect(classifySceneObjectSemantics(case1Scene, case1Scene.objects.find((o) => o.id === "canh_SA")!).strokeColor).toBe(0x1e293b);
    expect(resolveCertifiedRightAngleMarkers(case1Scene, case1Scene.objects).some((m) => m.footId === "B")).toBe(true);

    // Case 2: Đường cao SO không trùng bất kỳ cạnh bên nào
    const case2Scene = ({
      objects: [
        { id: "A", type: "point3", label: "Điểm A", notation: "A", origin: "free", render: "point_marker", xyz: ["-2", "-2", "0"] },
        { id: "B", type: "point3", label: "Điểm B", notation: "B", origin: "free", render: "point_marker", xyz: ["2", "-2", "0"] },
        { id: "C", type: "point3", label: "Điểm C", notation: "C", origin: "free", render: "point_marker", xyz: ["2", "2", "0"] },
        { id: "D", type: "point3", label: "Điểm D", notation: "D", origin: "free", render: "point_marker", xyz: ["-2", "2", "0"] },
        { id: "O", type: "point3", label: "Tâm O", notation: "O", origin: "derived", render: "point_marker", depends: ["A", "C"], xyz: ["0", "0", "0"] },
        { id: "S", type: "point3", label: "Đỉnh S", notation: "S", origin: "free", render: "point_marker", xyz: ["0", "0", "4"] },
        { id: "day_ABCD", type: "polygon3", label: "Đáy ABCD", notation: "ABCD", origin: "derived", surface_role: "BASE_REGION", formation_roles: ["CONSTRUCT_BASE"], depends: ["A", "B", "C", "D"], render: "filled_polygon", vertices: [["-2", "-2", "0"], ["2", "-2", "0"], ["2", "2", "0"], ["-2", "2", "0"]] },
        {
          id: "cao_SO",
          type: "segment3",
          label: "Đường cao SO",
          notation: "SO",
          origin: "derived",
          formation_roles: ["CONSTRUCT_HEIGHT"],
          depends: ["S", "O"],
          endpoint_ids: ["S", "O"],
          render: "segment",
          point_a: ["0", "0", "4"],
          point_b: ["0", "0", "0"],
          perpendicular_witness: {
            relation: "line_perpendicular_plane",
            status: "ENGINE_VERIFIED",
            from: "S",
            foot_id: "O",
            foot: ["0", "0", "0"],
            on: "day_ABCD",
            can_present_as_proven: true,
            plane_directions: [["4", "0", "0"], ["0", "4", "0"]],
            marker: { u: ["2", "-2", "0"], v: ["0", "0", "4"] },
          },
        },
        { id: "canh_SA", type: "segment3", label: "Cạnh SA", notation: "SA", origin: "derived", formation_roles: ["CONSTRUCT_LATERAL_BOUNDARY"], depends: ["S", "A"], endpoint_ids: ["S", "A"], render: "segment", point_a: ["0", "0", "4"], point_b: ["-2", "-2", "0"] },
      ],
      events: [
        { step_index: 0, action: "CREATE", object: "day_ABCD", objects: ["A", "B", "C", "D", "O", "S", "day_ABCD", "cao_SO", "canh_SA"], depends: [] },
      ],
    }) as unknown as Scene3D;
    expect(classifySceneObjectSemantics(case2Scene, case2Scene.objects.find((o) => o.id === "cao_SO")!).strokeColor).toBe(0x0f766e);
    expect(classifySceneObjectSemantics(case2Scene, case2Scene.objects.find((o) => o.id === "canh_SA")!).strokeColor).toBe(0x1e293b);
    expect(resolveCertifiedRightAngleMarkers(case2Scene, case2Scene.objects).some((m) => m.footId === "O")).toBe(true);

    // Case 3: Góc nhị diện với giao tuyến nghiêng SC (AK ⊥ SC, BK ⊥ SC tại K ∈ SC, góc phẳng nhị diện ∠AKB không suy biến)
    const case3Scene = ({
      objects: [
        { id: "S", type: "point3", label: "S", notation: "S", origin: "free", render: "point_marker", xyz: ["0", "0", "4"] },
        { id: "C", type: "point3", label: "C", notation: "C", origin: "free", render: "point_marker", xyz: ["0", "4", "0"] },
        { id: "A", type: "point3", label: "A", notation: "A", origin: "free", render: "point_marker", xyz: ["2", "3", "3"] },
        { id: "B", type: "point3", label: "B", notation: "B", origin: "free", render: "point_marker", xyz: ["1", "4", "4"] },
        { id: "K", type: "point3", label: "K", notation: "K", origin: "derived", role: "Hình chiếu của A lên SC", depends: ["A", "sc"], render: "point_marker", xyz: ["0", "2", "2"] },
        { id: "sc", type: "line3", label: "SC", notation: "SC", origin: "derived", depends: ["S", "C"], render: "line", point: ["0", "0", "4"], direction: ["0", "4", "-4"] },
        { id: "mp_SAC", type: "plane3", label: "(SAC)", notation: "(SAC)", origin: "derived", depends: ["S", "A", "C"], render: "plane_patch", point: ["0", "0", "4"], normal: ["-1", "1", "1"] },
        { id: "mp_SBC", type: "plane3", label: "(SBC)", notation: "(SBC)", origin: "derived", depends: ["S", "B", "C"], render: "plane_patch", point: ["0", "0", "4"], normal: ["-4", "1", "1"] },
        { id: "doan_AK", type: "segment3", label: "AK", notation: "AK", origin: "derived", depends: ["A", "K"], endpoint_ids: ["A", "K"], render: "segment", point_a: ["2", "3", "3"], point_b: ["0", "2", "2"] },
        { id: "doan_BK", type: "segment3", label: "BK", notation: "BK", origin: "derived", depends: ["B", "K"], endpoint_ids: ["B", "K"], render: "segment", point_a: ["1", "4", "4"], point_b: ["0", "2", "2"] },
        { id: "ak", type: "line3", label: "AK", notation: "AK", origin: "derived", depends: ["A", "K"], render: "line", point: ["0", "2", "2"], direction: ["2", "1", "1"] },
        { id: "bk", type: "line3", label: "BK", notation: "BK", origin: "derived", depends: ["B", "K"], render: "line", point: ["0", "2", "2"], direction: ["1", "2", "2"] },
        { id: "q_ak_sc", type: "quantity", label: "cos²(AK, SC)", origin: "derived", depends: ["ak", "sc"], value: "0", render: "readout" },
        { id: "q_bk_sc", type: "quantity", label: "cos²(BK, SC)", origin: "derived", depends: ["bk", "sc"], value: "0", render: "readout" },
        { id: "q_dih", type: "quantity", label: "Côsin bình phương của góc giữa (SAC) và (SBC)", origin: "derived", depends: ["mp_SAC", "mp_SBC"], value: "2/3", annotation: { kind: "angle", subject_ids: ["mp_SAC", "mp_SBC"], category: "result", role: "result" }, render: "readout" },
      ],
      events: [
        { step_index: 0, action: "CREATE", object: "mp_SAC", objects: ["S", "C", "A", "B", "K", "sc", "mp_SAC", "mp_SBC", "doan_AK", "doan_BK", "ak", "bk"], depends: [] },
        { step_index: 1, action: "MEASURE", object: "q_dih", objects: ["q_ak_sc", "q_bk_sc", "q_dih"], depends: ["mp_SAC", "mp_SBC"] },
      ],
    }) as unknown as Scene3D;
    const c3Markers = resolveCertifiedRightAngleMarkers(case3Scene, case3Scene.objects);
    expect(c3Markers.some((m) => m.footId === "K")).toBe(true);
    const c3Arcs = resolveVerifiedAngleArcs(case3Scene, case3Scene.objects);
    expect(c3Arcs.some((a) => a.vertexId === "K" && a.color === 0x2563eb)).toBe(true);

    // Case 4: Bài Oxyz hoàn toàn mới ngoài thư viện — (Q): 2x + y + 2z - 6 = 0, đường thẳng Δ qua P(0;0;1), N(3;2;3) cắt (Q) tại K(1; 2/3; 5/3), hình chiếu F(1; 1; 3/2)? Lấy số nguyên/hữu tỉ chính xác!
    // Chọn (Q): x + 2y + 2z - 9 = 0. N(3; 4; 5) -> n=(1,2,2), N.n - 9 = 3+8+10-9 = 12, |n|^2 = 9, t = 12/9 = 4/3 -> F = (3 - 4/3, 4 - 8/3, 5 - 8/3) = (5/3, 4/3, 7/3) thuộc (Q) vì 5/3 + 8/3 + 14/3 = 27/3 = 9!
    // Đường Δ qua K(1; 2; 2) ∈ (Q) (1 + 4 + 4 = 9!) và N(3; 4; 5).
    const case4OxyzScene = ({
      objects: [
        { id: "O", type: "point3", label: "Gốc tọa độ O(0; 0; 0)", notation: "O", role: "Gốc tọa độ Oxyz", origin: "free", render: "point_marker", xyz: ["0", "0", "0"] },
        { id: "K", type: "point3", label: "K(1; 2; 2)", notation: "K", role: "Giao điểm của Δ và (Q)", origin: "derived", depends: ["duong_delta", "mp_Q"], render: "point_marker", xyz: ["1", "2", "2"] },
        { id: "N", type: "point3", label: "N(3; 4; 5)", notation: "N", origin: "free", render: "point_marker", xyz: ["3", "4", "5"] },
        { id: "F", type: "point3", label: "F", notation: "F", role: "Hình chiếu của N lên (Q)", origin: "derived", depends: ["N", "mp_Q"], render: "point_marker", xyz: ["5/3", "4/3", "7/3"] },
        { id: "mp_Q", type: "plane3", label: "Mặt phẳng (Q): x + 2y + 2z - 9 = 0", notation: "(Q)", role: "Mặt phẳng tọa độ x + 2y + 2z - 9 = 0", origin: "free", render: "plane_patch", point: ["1", "2", "2"], normal: ["1", "2", "2"] },
        { id: "duong_delta", type: "line3", label: "Đường thẳng Δ", notation: "Δ", role: "Đường thẳng qua K và N", origin: "free", depends: ["K", "N"], render: "line", point: ["1", "2", "2"], direction: ["2", "2", "3"] },
        { id: "doan_NF", type: "segment3", label: "NF", notation: "NF", origin: "derived", depends: ["N", "F"], endpoint_ids: ["N", "F"], render: "segment", point_a: ["3", "4", "5"], point_b: ["5/3", "4/3", "7/3"] },
        { id: "doan_FK", type: "segment3", label: "FK", notation: "FK", origin: "derived", depends: ["F", "K"], endpoint_ids: ["F", "K"], render: "segment", point_a: ["5/3", "4/3", "7/3"], point_b: ["1", "2", "2"] },
        { id: "nf", type: "line3", label: "NF", notation: "NF", origin: "derived", depends: ["N", "F"], render: "line", point: ["3", "4", "5"], direction: ["-4/3", "-8/3", "-8/3"] },
        { id: "fk", type: "line3", label: "FK", notation: "FK", origin: "derived", depends: ["F", "K"], render: "line", point: ["5/3", "4/3", "7/3"], direction: ["-2/3", "2/3", "-1/3"] },
        { id: "q_perp_nf_fk", type: "quantity", label: "cos²(NF, FK)", origin: "derived", depends: ["nf", "fk"], value: "0", render: "readout" },
        { id: "q_angle_line_plane", type: "quantity", label: "Góc giữa Δ và (Q)", origin: "derived", depends: ["duong_delta", "mp_Q"], value: "16/17", annotation: { kind: "angle", subject_ids: ["duong_delta", "mp_Q"], category: "result", role: "result" }, render: "readout" },
      ],
      events: [
        { step_index: 0, action: "CREATE", object: "mp_Q", objects: ["O", "N", "mp_Q", "duong_delta", "K", "F", "doan_NF", "doan_FK", "nf", "fk"], depends: [] },
        { step_index: 1, action: "MEASURE", object: "q_angle_line_plane", objects: ["q_perp_nf_fk", "q_angle_line_plane"], depends: ["duong_delta", "mp_Q"] },
      ],
    }) as unknown as Scene3D;
    expect(isExplicitOxyzCoordinateScene(case4OxyzScene)).toBe(true);
    expect(classifySceneObjectSemantics(case4OxyzScene, case4OxyzScene.objects.find((o) => o.id === "mp_Q")!).strokeColor).toBe(0x6d28d9);
    expect(classifySceneObjectSemantics(case4OxyzScene, case4OxyzScene.objects.find((o) => o.id === "duong_delta")!).strokeColor).toBe(0x2563eb);
    expect(classifySceneObjectSemantics(case4OxyzScene, case4OxyzScene.objects.find((o) => o.id === "doan_NF")!).strokeColor).toBe(0x0f766e);
    expect(resolveCertifiedRightAngleMarkers(case4OxyzScene, case4OxyzScene.objects).some((m) => m.footId === "F")).toBe(true);
    expect(resolveVerifiedAngleArcs(case4OxyzScene, case4OxyzScene.objects).some((a) => a.vertexId === "K" && a.color === 0x2563eb)).toBe(true);

    // Case 5: Hai đường chéo nhau AB (trên z=0, y=0) và CD (trên z=3, x=0) có đoạn vuông góc chung MN nối M(0,0,0) và N(0,0,3)
    const case5SkewScene = ({
      objects: [
        { id: "A", type: "point3", label: "A", notation: "A", origin: "free", render: "point_marker", xyz: ["-2", "0", "0"] },
        { id: "B", type: "point3", label: "B", notation: "B", origin: "free", render: "point_marker", xyz: ["3", "0", "0"] },
        { id: "C", type: "point3", label: "C", notation: "C", origin: "free", render: "point_marker", xyz: ["0", "-2", "3"] },
        { id: "D", type: "point3", label: "D", notation: "D", origin: "free", render: "point_marker", xyz: ["0", "3", "3"] },
        { id: "M", type: "point3", label: "M", notation: "M", origin: "derived", depends: ["ab"], render: "point_marker", xyz: ["0", "0", "0"] },
        { id: "N", type: "point3", label: "N", notation: "N", origin: "derived", depends: ["cd"], render: "point_marker", xyz: ["0", "0", "3"] },
        { id: "ab", type: "line3", label: "AB", notation: "AB", origin: "derived", depends: ["A", "B"], render: "line", point: ["0", "0", "0"], direction: ["1", "0", "0"] },
        { id: "cd", type: "line3", label: "CD", notation: "CD", origin: "derived", depends: ["C", "D"], render: "line", point: ["0", "0", "3"], direction: ["0", "1", "0"] },
        { id: "doan_MN", type: "segment3", label: "MN", notation: "MN", origin: "derived", depends: ["M", "N"], endpoint_ids: ["M", "N"], render: "segment", point_a: ["0", "0", "0"], point_b: ["0", "0", "3"] },
        {
          id: "kc_AB_CD",
          type: "quantity",
          label: "Khoảng cách giữa AB và CD",
          origin: "derived",
          depends: ["ab", "cd"],
          value: "3",
          render: "readout",
          annotation: {
            kind: "distance",
            subject_ids: ["ab", "cd"],
            category: "result",
            role: "result",
            witness: {
              from: "cd",
              from_point: ["0", "0", "3"],
              foot: ["0", "0", "0"],
              on: "ab",
              relation: "common_perpendicular",
              marker: { u: ["3", "0", "0"], v: ["0", "0", "3"], u_to: "B" },
              second: {
                foot: ["0", "0", "3"],
                on: "cd",
                marker: { u: ["0", "3", "0"], v: ["0", "0", "-3"], u_to: "D" },
              },
            },
          },
        },
      ],
      events: [
        { step_index: 0, action: "CREATE", object: "doan_MN", objects: ["A", "B", "C", "D", "ab", "cd", "M", "N", "doan_MN"], depends: [] },
        { step_index: 1, action: "MEASURE", object: "kc_AB_CD", objects: ["kc_AB_CD"], depends: ["ab", "cd"] },
      ],
    }) as unknown as Scene3D;
    const case5Plan = buildPedagogicalConstructionPlan(case5SkewScene);
    expect(classifySceneObjectSemantics(case5Plan.scene, case5Plan.scene.objects.find((o) => o.id === "ab")!).strokeColor).toBe(0x2563eb);
    expect(classifySceneObjectSemantics(case5Plan.scene, case5Plan.scene.objects.find((o) => o.id === "cd")!).strokeColor).toBe(0x2563eb);
    expect(classifySceneObjectSemantics(case5Plan.scene, case5Plan.scene.objects.find((o) => o.id === "doan_MN")!).strokeColor).toBe(0x0f766e);
    const c5Markers = resolveCertifiedRightAngleMarkers(case5Plan.scene, case5Plan.scene.objects);
    expect(c5Markers.some((m) => m.footId === "M")).toBe(true);
    expect(c5Markers.some((m) => m.footId === "N")).toBe(true);

    // Case 6: Cảnh có nhiều đối tượng trùng nhau (trục Oz + đường cao OS + cạnh bên chóp + đường mang phụ os)
    const case6CoincideAxes = dungTrucOxyzSuPham(
      [new THREE.Vector3(4, 0, 0), new THREE.Vector3(0, 4, 0), new THREE.Vector3(0, 0, 4)],
      {
        hasExplicitOriginLabel: true,
        activeSegments: [[new THREE.Vector3(0, 0, 0), new THREE.Vector3(0, 0, 4)]],
      },
    );
    const ozPosLine = case6CoincideAxes.getObjectByName("truc:Oz:duong") as THREE.Line | undefined;
    expect(ozPosLine).toBeDefined();
    const ozPosAttr = ozPosLine!.geometry.getAttribute("position");
    // Phần dương trục Oz bắt đầu từ z >= 4 (nhường đoạn [0, 4] cho đường cao OS để không chồng hai nét trùng nhau!)
    expect(ozPosAttr.getZ(0)).toBeGreaterThanOrEqual(3.99);

    // Case 7: Quan hệ hình học chưa xác minh (provenance UNVERIFIED / góc không vuông thật) -> Fail-closed: KHÔNG vẽ ký hiệu ⊥ hoặc cung góc sai!
    const case7UnverifiedScene = ({
      objects: [
        { id: "A", type: "point3", label: "A", notation: "A", origin: "free", render: "point_marker", xyz: ["0", "0", "0"] },
        { id: "B", type: "point3", label: "B", notation: "B", origin: "free", render: "point_marker", xyz: ["3", "0", "0"] },
        { id: "S", type: "point3", label: "S", notation: "S", origin: "free", render: "point_marker", xyz: ["1", "0", "4"], source: { provenance: "UNVERIFIED", is_given: false } },
        {
          id: "fake_perp",
          type: "segment3",
          label: "SA",
          notation: "SA",
          origin: "derived",
          depends: ["S", "A"],
          endpoint_ids: ["S", "A"],
          render: "segment",
          point_a: ["1", "0", "4"],
          point_b: ["0", "0", "0"],
          source: { provenance: "UNVERIFIED", is_given: false },
          perpendicular_witness: {
            relation: "line_perp_line",
            from: "S",
            foot_id: "A",
            foot: ["0", "0", "0"],
            on: "B",
            can_present_as_proven: false,
            marker: { u: ["3", "0", "0"], v: ["1", "0", "4"] },
          },
        },
        {
          id: "fake_angle",
          type: "quantity",
          label: "Góc giữa SA và AB",
          origin: "derived",
          depends: ["fake_perp"],
          value: "1/2",
          source: { provenance: "UNVERIFIED", is_given: false },
          annotation: { kind: "angle", subject_ids: ["fake_perp"], category: "result", role: "result" },
          render: "readout",
        },
      ],
      events: [
        { step_index: 0, action: "CREATE", object: "fake_perp", objects: ["A", "B", "S", "fake_perp", "fake_angle"], depends: [] },
      ],
    }) as unknown as Scene3D;
    expect(resolveCertifiedRightAngleMarkers(case7UnverifiedScene, case7UnverifiedScene.objects)).toHaveLength(0);
    expect(resolveVerifiedAngleArcs(case7UnverifiedScene, case7UnverifiedScene.objects)).toHaveLength(0);
  });
});
