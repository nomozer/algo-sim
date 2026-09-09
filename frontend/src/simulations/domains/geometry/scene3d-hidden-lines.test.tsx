import { describe, expect, it } from "vitest";
import * as THREE from "three";
import { buildObject3D } from "./scene3d-view";
import type { SceneObject } from "./scene3d-model";

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

  it("cạnh khối dựng HAI lượt: một liền, một đứt", () => {
    const con = gom(buildObject3D(KHOI, false)!);
    const thay = con.find((c) => c.name.endsWith(":thay"));
    const khuat = con.find((c) => c.name.endsWith(":khuat"));
    expect(thay).toBeDefined();
    expect(khuat).toBeDefined();
    const mt = (thay as THREE.Line).material as THREE.Material;
    const mk = (khuat as THREE.Line).material as THREE.Material;
    // Phần thấy vẽ khi KHÔNG bị che; phần khuất vẽ khi BỊ che. Hai phép kiểm
    // chiều sâu ngược nhau — đó là toàn bộ cơ chế, không có bước phân loại nào
    // trên CPU để lỗi thời khi camera đổi.
    expect(mt.depthFunc).toBe(THREE.LessEqualDepth);
    expect(mk.depthFunc).toBe(THREE.GreaterDepth);
    expect((mk as THREE.LineDashedMaterial).dashSize).toBeGreaterThan(0);
  });

  /* Không có `polygonOffset`, một vành đáy nằm ĐÚNG trên mặt khối sẽ nhấp nháy
     giữa "thấy" và "khuất" theo sai số chiều sâu — và nhấp nháy đọc ra như một
     lỗi hình học chứ không như một lỗi hiển thị. */
  it("đường có `polygonOffset` để không nhấp nháy khi nằm trên mặt khối", () => {
    const con = gom(buildObject3D(KHOI, false)!);
    for (const ten of [":thay", ":khuat"]) {
      const d = con.find((c) => c.name.endsWith(ten)) as THREE.Line;
      expect((d.material as THREE.Material).polygonOffset).toBe(true);
    }
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
});
