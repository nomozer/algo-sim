import { describe, expect, it } from "vitest";
import * as THREE from "three";
import {
  buildObject3D,
  canonicalEdgeMaterial,
  classifySolidEdgeVisibility,
  datCoDauDinh,
  datKhungNhin,
  doanNhuongCanh,
  lamDiu,
  updateCanonicalEdgeVisibility,
} from "./scene3d-view";
import type { SceneObject } from "./scene3d-model";
import { DAU_DINH_PX, banKinhBamPx, coDauDinhPx, donViMoiPx } from "./pick-target";

/**
 * NÉT LIỀN / NÉT KHUẤT THEO CAMERA — hợp đồng CẤU TRÚC.
 *
 * ─── TEST NÀY KHOÁ GÌ, VÀ CỐ Ý KHÔNG KHOÁ GÌ ─────────────────────────────
 *
 * Câu *"đoạn này có bị che không"* do GPU trả lời theo từng điểm ảnh, và chỉ
 * kiểm được trong trình duyệt thật (`certify-scene3d-hidden-lines.mjs`). Ở đây
 * khoá **những mảnh cấu trúc làm cho việc ấy khả thi** — vì thiếu một mảnh thì
 * hidden-line không hỏng ồn ào, nó **biến mất im lặng**, đúng cách nó đã vắng
 * mặt suốt từ đầu: mọi khối khai `depthWrite: false`, nên không gì che được gì
 * và một cạnh sau quả cầu vẽ y hệt cạnh trước nó.
 *
 * Tách khỏi `scene3d.test.tsx` vì file ấy cố ý **không nhập `three`**; những
 * khẳng định dưới đây phải so với hằng số thật của thư viện (`LessEqualDepth`,
 * `GreaterDepth`) chứ không phải với con số ma.
 */
describe("hidden-line — cấu trúc cảnh", () => {
  const KHOI: SceneObject = {
    id: "K", label: "Khối", type: "solid", render: "mesh",
    origin: "derived", producer: "construct_solid", depends: [],
    vertices: [["0", "0", "0"], ["2", "0", "0"], ["0", "2", "0"], ["0", "0", "2"]],
    vertex_ids: ["A", "B", "C", "S"],
    faces: [[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]],
  };
  const CAU: SceneObject = {
    id: "S", label: "Cầu", type: "curved_solid", render: "curved_solid",
    origin: "derived", producer: "construct_curved_solid", depends: [],
    curved_kind: "ball", anchor: ["0", "0", "0"], apex_or_top: null,
    rim_point: ["3", "0", "0"], radius_sq: "9", height_sq: "0",
  };

  const gom = (o: THREE.Object3D) => {
    const ra: THREE.Object3D[] = [];
    o.traverse((c) => ra.push(c));
    return ra;
  };

  it.each([["khối đa diện", KHOI], ["khối cong", CAU]] as const)(
    "%s mang lớp chiều sâu VÔ HÌNH — không có nó thì không gì che được gì",
    (_ten, vat) => {
      const con = gom(buildObject3D(vat, false)!);
      const cs = con.filter((c) => c.userData?.chieuSau);
      expect(cs).toHaveLength(1);
      const m = (cs[0] as THREE.Mesh).material as THREE.Material
        & { colorWrite: boolean; depthWrite: boolean };
      expect(m.colorWrite).toBe(false);   // vô hình
      expect(m.depthWrite).toBe(true);    // nhưng CÓ ghi chiều sâu
      // …và lùi một chút: cạnh nằm trên mặt không được tranh chiều sâu với nó
      expect((m as THREE.Material).polygonOffset).toBe(true);
      expect((m as THREE.Material).polygonOffsetFactor).toBeGreaterThan(0);
    },
  );

  /* Miếng mặt phẳng là vật MINH HOẠ, cỡ do tầng trình bày tự chọn. Cho nó che
     khuất thì một quyết định trình bày bắt đầu quyết định thứ học sinh đọc ra
     là "nằm trước" hay "nằm sau" — tức một mệnh đề hình học. */
  it("miếng mặt phẳng KHÔNG được ghi chiều sâu", () => {
    const mp: SceneObject = {
      id: "P", label: "Mặt phẳng", type: "plane3", render: "surface",
      origin: "derived", producer: "construct_plane", depends: [],
      point: ["0", "0", "0"], normal: ["0", "0", "1"],
    };
    const con = gom(buildObject3D(mp, false)!);
    expect(con.filter((c) => c.userData?.chieuSau)).toHaveLength(0);
  });

  it("mỗi cạnh khối có đúng MỘT visual owner", () => {
    const con = gom(buildObject3D(KHOI, false)!);
    const owners = con.filter((c) => c.userData?.visualOwnerId);
    expect(owners).toHaveLength(6);
    expect(new Set(owners.map((c) => c.userData.visualOwnerId)).size).toBe(6);
  });

  it("visible dùng nét liền, hidden dùng nét đứt", () => {
    expect(canonicalEdgeMaterial(false, false)).toBeInstanceOf(THREE.LineBasicMaterial);
    expect(canonicalEdgeMaterial(true, false)).toBeInstanceOf(THREE.LineDashedMaterial);
  });

  /* w10 — ảnh w09: cạnh AB, AD của hình chóp đáy chữ nhật được PHÂN LOẠI khuất
     đúng, nhưng không có một điểm ảnh nào. Đoạn khuất nằm sau lớp chiều sâu của
     chính khối nó, nên phép kiểm chiều sâu mặc định của GPU loại nó lần hai. */
  /* Nét ĐỤC nằm hàng đợi opaque, vẽ TRƯỚC mọi mặt tô trong suốt — nên mặt tô
     phủ lên nét và cạnh SC giữa hai mặt trước đọc ra xám nhạt (ảnh w10). Nét
     phải cùng hàng đợi trong suốt để `renderOrder` xếp nó SAU mặt. */
  it("nét thấy vẽ SAU mặt tô, không bị mặt tô phủ lên", () => {
    expect(canonicalEdgeMaterial(false, false).transparent).toBe(true);
    expect(canonicalEdgeMaterial(false, false).opacity).toBe(1);
  });

  /* Thực nghiệm w10 (cùng góc, hai bản dựng): nét thấy CÓ kiểm chiều sâu thì
     cạnh SC giữa hai mặt trước nhạt đi — mẫu MSAA hai bên nét trượt phép kiểm
     với lớp chiều sâu của chính khối. Tắt kiểm ⇒ SC đậm như SD. Phân loại CPU
     (thứ oracle đo) là thẩm quyền duy nhất cho cả hai lớp. */
  it("nét thấy cũng không bị GPU kiểm chiều sâu lần hai", () => {
    expect(canonicalEdgeMaterial(false, false).depthTest).toBe(false);
  });

  it("đoạn đã phân loại KHUẤT không bị GPU loại lần hai", () => {
    const m = canonicalEdgeMaterial(true, false);
    expect(m.depthTest).toBe(false);
    expect(m.opacity).toBeGreaterThanOrEqual(0.85);
  });

  it("nét cạnh dùng mực riêng, tương phản với mặt tô (≥ 7:1 trên nền sáng)", () => {
    const sang = (c: THREE.Color) => {
      const k = (x: number) => (x <= 0.03928 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4);
      const s = c.clone().convertLinearToSRGB();
      return 0.2126 * k(s.r) + 0.7152 * k(s.g) + 0.0722 * k(s.b);
    };
    const con = gom(buildObject3D(KHOI, false)!);
    const mat = con.filter((c) => (c as THREE.Line).isLine && c.parent?.userData?.visualOwnerId)
      .map((c) => (c as THREE.Line).material as THREE.LineBasicMaterial);
    expect(mat.length).toBeGreaterThan(0);
    const to = ((con.find((c) => (c as THREE.Mesh).isMesh && !c.userData?.chieuSau) as THREE.Mesh)
      .material as THREE.MeshStandardMaterial).color;
    for (const m of mat) {
      expect(m.color.getHex()).not.toBe(to.getHex());
      expect(1.05 / (sang(m.color) + 0.05)).toBeGreaterThanOrEqual(7);
    }
  });

  /* w10 — một cạnh, MỘT nét. Đoạn `SA` trùng cạnh S-A của khối: khi khối đã có
     mặt thì cạnh chuẩn vẽ, đoạn chỉ còn là vùng bấm (và dấu góc vuông). Trước
     khi khối xuất hiện thì đoạn vẫn tự vẽ — không mất nét nào giữa các bước. */
  const DOAN: SceneObject = {
    id: "chieu_cao_SA", label: "Chiều cao SA", type: "segment3", render: "segment",
    origin: "derived", producer: "construct_segment", depends: ["A", "S"],
    point_a: ["0", "0", "2"], point_b: ["0", "0", "0"], endpoint_ids: ["S", "A"],
    boundary_edge_ids: ["K::edge:A-S"],
  } as SceneObject;
  const KHOI_CO_CHU = { ...KHOI, edge_ownership: [
    { edge_id: "K::edge:A-S", endpoint_ids: ["A", "S"], adjacent_surface_ids: [] },
  ] } as SceneObject;

  it("đoạn trùng cạnh khối nhường nét khi khối CÓ MẶT, tự vẽ khi chưa", () => {
    expect([...doanNhuongCanh([DOAN, KHOI_CO_CHU], () => "0")]).toEqual(["chieu_cao_SA"]);
    expect([...doanNhuongCanh([DOAN], () => "0")]).toEqual([]);
    // tách khối: khối đã dời chỗ thì nét của đoạn không còn trùng cạnh nào
    expect([...doanNhuongCanh([DOAN, KHOI_CO_CHU], (id) => (id === "K" ? "1" : "0"))]).toEqual([]);
  });

  it("đoạn nhường nét không để lại nét nhìn thấy nào, trừ dấu góc vuông", () => {
    const con = gom(buildObject3D({ ...DOAN, display_role: "hit_proxy" } as SceneObject, false)!);
    const thay = con.filter((c) => (c as THREE.Line).isLine
      && ((c as THREE.Line).material as THREE.Material & { colorWrite: boolean }).colorWrite !== false);
    expect(thay.map((c) => c.name)).toEqual(["perp_marker:chieu_cao_SA"]);
    expect(con.some((c) => (c as THREE.Line).isLine && c.name.includes("proxy"))).toBe(true);
  });

  /* w10 — causal phân tầng: đích đậm nhất, vật ngoài chuỗi làm dịu. Làm dịu
     phải sống qua lần dựng lại cạnh khi XOAY, nếu không orbit một cái là cả
     hình sáng trở lại trong khi ô soi vẫn mở. */
  it("tầng đích tô cạnh bằng màu đích; nét đứt giữ nguyên", () => {
    const con = gom(buildObject3D(KHOI, "dich")!);
    const canh = con.filter((c) => (c as THREE.Line).isLine && c.parent?.userData?.visualOwnerId)
      .map((c) => (c as THREE.Line).material as THREE.LineBasicMaterial);
    expect(new Set(canh.map((m) => m.color.getHex()))).toEqual(new Set([0xc2410c]));
    expect(canh.some((m) => m instanceof THREE.LineDashedMaterial)).toBe(true);
  });

  it("làm dịu vật ngoài chuỗi sống qua lần dựng lại cạnh khi xoay", () => {
    const goc = new THREE.Group();
    const khoi = buildObject3D(KHOI, false)!;
    goc.add(khoi);
    lamDiu(khoi);
    const cam = new THREE.PerspectiveCamera(50, 1, 0.1, 100);
    for (const [x, y, z] of [[5, 5, 5], [-5, -5, 5]]) {
      cam.position.set(x, y, z);
      cam.lookAt(0, 0, 0);
      cam.updateMatrixWorld();
      updateCanonicalEdgeVisibility(goc, cam);
      const op = gom(khoi).filter((c) => (c as THREE.Line).isLine && c.parent?.userData?.visualOwnerId)
        .map((c) => ((c as THREE.Line).material as THREE.Material).opacity);
      expect(op.length).toBeGreaterThan(0);
      expect(Math.max(...op)).toBeLessThanOrEqual(0.3 + 1e-9);
    }
  });

  /* w10 — "Xem lại toàn hình" ngay sau một cú kéo: OrbitControls còn giữ ĐÀ
     xoay (damping), nên camera đặt về khung rồi vẫn trôi theo cú kéo cũ và
     không bao giờ về trạng thái trung tính (runner orbit đo: PFPFP). */
  it("đặt khung nhìn HUỶ đà xoay còn lại — camera đứng yên ở khung mới", async () => {
    const { OrbitControls } = await import("three/addons/controls/OrbitControls.js");
    const nut = { addEventListener() {}, removeEventListener() {} };
    const dom = { ...nut, style: {}, ownerDocument: nut, getRootNode: () => nut,
      clientWidth: 800, clientHeight: 600 } as unknown as HTMLElement;
    const cam = new THREE.PerspectiveCamera(50, 4 / 3, 0.1, 100);
    cam.up.set(0, 0, 1);
    cam.position.set(5, 5, 5);
    const dk = new OrbitControls(cam, dom);
    dk.enableDamping = true;
    dk.update();
    (dk as unknown as { _sphericalDelta: THREE.Spherical })._sphericalDelta.theta = 0.8; // đà của cú kéo
    datKhungNhin(cam, dk, { viTri: [8, 3, 6], nhinVao: [0, 0, 0] });
    for (let i = 0; i < 60; i++) dk.update();
    expect(cam.position.distanceTo(new THREE.Vector3(8, 3, 6))).toBeLessThan(1e-9);
  });

  it("highlight chỉ đổi màu, không đổi solid/dashed policy", () => {
    expect(canonicalEdgeMaterial(false, true)).toBeInstanceOf(THREE.LineBasicMaterial);
    expect(canonicalEdgeMaterial(true, true)).toBeInstanceOf(THREE.LineDashedMaterial);
  });

  it("orbit tính lại hidden/visible classification", () => {
    const front = classifySolidEdgeVisibility(KHOI, new THREE.Vector3(5, 5, 5));
    const back = classifySolidEdgeVisibility(KHOI, new THREE.Vector3(-5, -5, -5));
    expect(front.visible_edge_ids.length).toBeGreaterThan(0);
    expect(front.hidden_edge_ids.length).toBeGreaterThan(0);
    expect(back.visible_edge_ids).not.toEqual(front.visible_edge_ids);
    expect(front.mixed_edge_ids).toEqual([]);
    expect(back.mixed_edge_ids).toEqual([]);
  });

  it("machine edge id giữ endpoint order theo vertex ordinal, không theo display text", () => {
    const ordinal: SceneObject = {
      ...KHOI,
      id: "ordinal",
      vertex_ids: ["Z", "A", "C", "S"],
    };
    const ids = classifySolidEdgeVisibility(
      ordinal,
      new THREE.Vector3(5, 5, 5),
    ).visible_edge_ids.concat(
      classifySolidEdgeVisibility(ordinal, new THREE.Vector3(5, 5, 5)).hidden_edge_ids,
    );
    expect(ids).toContain("ordinal::edge:Z-A");
    expect(ids).not.toContain("ordinal::edge:A-Z");
  });

  it("cạnh bị một mặt không kề che một phần được phân loại MIXED", () => {
    const partial: SceneObject = {
      id: "partial", label: "Synthetic partial occluder", type: "solid", render: "mesh",
      origin: "derived", producer: "construct_solid", depends: [],
      vertices: [
        ["-2", "0", "0"], ["2", "0", "0"], ["0", "-2", "0"],
        ["0", "-1", "1"], ["2", "-1", "1"], ["1", "1", "1"],
      ],
      vertex_ids: ["A", "B", "C", "P", "Q", "R"],
      faces: [[0, 1, 2], [3, 4, 5]],
    };
    const audit = classifySolidEdgeVisibility(partial, new THREE.Vector3(0, 0, 5));
    expect(audit.mixed_edge_ids).toContain("partial::edge:A-B");
    expect(audit.visible_edge_ids).not.toContain("partial::edge:A-B");
    expect(audit.hidden_edge_ids).not.toContain("partial::edge:A-B");
  });

  it("thiết diện viền đã khép nhưng CHƯA tới bước khép: vẽ đủ viền, chưa tô mặt", () => {
    const td = {
      id: "T", label: "Thiết diện", type: "section", render: "polygon",
      origin: "derived", producer: "construct_section", depends: [],
      polygon: [["0", "0", "1"], ["1", "0", "1"], ["1", "1", "1"], ["0", "1", "1"]],
      closed: true, fill_visible: false,
    } as SceneObject;
    const con = gom(buildObject3D(td, false)!);
    expect(con.some((c) => (c as THREE.Mesh).isMesh)).toBe(false);
    const vien = con.find((c) => (c as THREE.Line).isLine) as THREE.Line;
    expect(vien.geometry.getAttribute("position").count).toBe(5);   // 4 đỉnh + quay về đầu
    expect(gom(buildObject3D({ ...td, fill_visible: true } as SceneObject, false)!)
      .some((c) => (c as THREE.Mesh).isMesh)).toBe(true);
  });

  it("BASE_REGION tham chiếu canonical boundary không tự vẽ owner thứ hai", () => {
    const base = {
      id: "base", label: "Đáy ABC", type: "polygon3", render: "polygon",
      origin: "free", producer: null, depends: ["A", "B", "C"],
      vertices: [["0", "0", "0"], ["2", "0", "0"], ["0", "2", "0"]],
      vertex_ids: ["A", "B", "C"],
      surface_role: "BASE_REGION",
      occludes_edges: false,
      boundary_edge_ids: ["K::edge:A-B", "K::edge:B-C", "K::edge:A-C"],
    } as SceneObject;
    const rendered = buildObject3D(base, true)!;
    expect(gom(rendered).filter((child) => (child as THREE.Line).isLine)).toHaveLength(0);
  });

  it("thiết diện KHÔNG còn `depthTest: false` — phần khuất phải đọc ra là khuất", () => {
    const elip: SceneObject = {
      id: "E", label: "Elip", type: "ellipse3", render: "ellipse",
      origin: "derived", producer: "intersect_plane_curved", depends: [],
      center: ["0", "0", "0"], normal: ["0", "0", "1"],
      major_dir: ["1", "0", "0"], minor_dir: ["0", "1", "0"],
      semi_major_sq: "4", semi_minor_sq: "1",
    };
    const con = gom(buildObject3D(elip, false)!);
    const mats = con.filter((c) => (c as THREE.Mesh).isMesh)
      .map((c) => (c as THREE.Mesh).material as THREE.Material);
    expect(mats.length).toBeGreaterThanOrEqual(2);
    expect(mats.every((m) => m.depthTest !== false)).toBe(true);
    expect(mats.some((m) => m.depthFunc === THREE.LessEqualDepth)).toBe(true);
    expect(mats.some((m) => m.depthFunc === THREE.GreaterDepth)).toBe(true);
  });

  it("đường tròn thiết diện cũng có hai lượt", () => {
    const dt: SceneObject = {
      id: "C", label: "Đường tròn", type: "circle3", render: "circle",
      origin: "derived", producer: "intersect_plane_curved", depends: [],
      center: ["0", "0", "0"], normal: ["0", "0", "1"], radius_sq: "4",
    };
    const mats = gom(buildObject3D(dt, false)!)
      .filter((c) => (c as THREE.Mesh).isMesh)
      .map((c) => (c as THREE.Mesh).material as THREE.Material);
    expect(mats.some((m) => m.depthFunc === THREE.LessEqualDepth)).toBe(true);
    expect(mats.some((m) => m.depthFunc === THREE.GreaterDepth)).toBe(true);
  });

  /* Lớp chiều sâu là chi tiết TRÌNH BÀY. Nó không được trở thành một vật của
     cảnh: không bắt chuột, không vào hộp bao khung nhìn, không có id ngữ
     nghĩa. Ba khẳng định dưới đây là ba đường nó có thể rò ra. */
  it("lớp chiều sâu không mang id ngữ nghĩa và không đổi số vật của cảnh", () => {
    const con = gom(buildObject3D(KHOI, false)!);
    const cs = con.find((c) => c.userData?.chieuSau)!;
    expect(cs.name).toBe("");
    // dùng CHUNG hình học với khối ⇒ không thêm một tam giác nào
    const khoi = con.find((c) => (c as THREE.Mesh).isMesh && !c.userData?.chieuSau);
    expect((cs as THREE.Mesh).geometry)
      .toBe((khoi as THREE.Mesh).geometry);
  });

  /* w11 — review W10-H6: ngữ cảnh cấu trúc NHẸ hơn mọi tầng nhấn mạnh. Nó giữ
     mực trung tính (không tô màu tầng, không làm dịu); chỉ vật ngoài bao đóng
     mới dịu. Và "cam = vật mới dựng" phải là cam thật, đọc được trên nền sáng. */
  const mauCanh = (o: THREE.Object3D) => new Set(gom(o)
    .filter((c) => (c as THREE.Line).isLine && c.parent?.userData?.visualOwnerId)
    .map((c) => ((c as THREE.Line).material as THREE.LineBasicMaterial).color.getHex()));

  it("tầng ngữ cảnh giữ mực cạnh trung tính", () => {
    expect(mauCanh(buildObject3D(KHOI, "boi_canh")!)).toEqual(mauCanh(buildObject3D(KHOI, false)!));
  });

  it("vật mới dựng ở bước (formation) mang màu cam, không vàng nhạt", () => {
    const [mau] = [...mauCanh(buildObject3D(KHOI, true)!)];
    const c = new THREE.Color(mau);
    const hsl = { h: 0, s: 0, l: 0 };
    c.getHSL(hsl, THREE.SRGBColorSpace);   // mặc định là không gian TUYẾN TÍNH
    expect(hsl.h * 360).toBeGreaterThan(15);
    expect(hsl.h * 360).toBeLessThan(35);   // cam: 15°–35°, không phải hổ phách/vàng
    expect(hsl.l).toBeLessThan(0.5);        // đủ đậm cho nét 1 px trên nền sáng
  });
});

// ══ w11 · CHẤM ĐỈNH THEO ĐIỂM ẢNH · ĐƯỜNG PHỤ NHẸ Ở TRẠNG THÁI CUỐI ═════════
describe("w11 · chấm đỉnh và đường phụ", () => {
  const DIEM: SceneObject = {
    id: "A", label: "A", type: "point3", render: "point_marker",
    origin: "free", producer: null, depends: [], xyz: ["0", "0", "0"],
  };
  const DUONG: SceneObject = {
    id: "BD", label: "Đường thẳng BD", type: "line3", render: "line",
    origin: "derived", producer: "construct_line", depends: ["B", "D"],
    point: ["0", "0", "0"], direction: ["1", "1", "0"],
  };
  const duKien = (o: THREE.Object3D, ten: string) => {
    let ra: THREE.Object3D | undefined;
    o.traverse((x) => { if (x.userData?.[ten]) ra = x; });
    return ra!;
  };
  const gom = (o: THREE.Object3D) => {
    const ra: THREE.Object3D[] = [];
    o.traverse((x) => { ra.push(x); });
    return ra;
  };

  it("chấm và vùng bấm chiếu ra đúng token px CSS ở mọi khoảng camera", () => {
    for (const [kc, chon, rong, px] of [
      [6, false, 1000, DAU_DINH_PX.thuong], [20, false, 1000, DAU_DINH_PX.thuong],
      [12, false, 360, coDauDinhPx(false, 360)], [12, true, 1000, DAU_DINH_PX.chon],
    ] as const) {
      const goc = new THREE.Group();
      goc.add(buildObject3D(DIEM, chon ? "dich" : false)!);
      const cam = new THREE.PerspectiveCamera(50, 1, 0.1, 100);
      cam.position.set(0, -kc, 0);
      cam.lookAt(0, 0, 0);
      cam.updateMatrixWorld();
      datCoDauDinh(goc, cam, rong, 480);
      const donVi = donViMoiPx(kc, 50, 480);
      const cham = duKien(goc, "dauDinh") as THREE.Mesh;
      const r = (cham.geometry as THREE.SphereGeometry).parameters.radius * cham.scale.x;
      expect((2 * r) / donVi).toBeCloseTo(px, 6);
      const bam = duKien(goc, "vungBam") as THREE.Mesh;
      const rb = (bam.geometry as THREE.SphereGeometry).parameters.radius * bam.scale.x;
      expect(rb / donVi).toBeCloseTo(banKinhBamPx(rong), 6);
    }
  });

  it("đường vô hạn không được nhấn thì nhạt; đang dựng/được chọn thì rõ", () => {
    const op = (o: THREE.Object3D) => gom(o).filter((c) => (c as THREE.Line).isLine)
      .map((c) => ((c as THREE.Line).material as THREE.Material).opacity);
    expect(Math.max(...op(buildObject3D(DUONG, false)!))).toBeLessThanOrEqual(0.5);
    expect(Math.max(...op(buildObject3D(DUONG, true)!))).toBe(1);
  });
});
