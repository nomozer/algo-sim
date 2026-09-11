/**
 * scene3d-visual-language.test.tsx — khoá NGÔN NGỮ HÌNH HỌC đã được duyệt
 * (vòng mockup tĩnh, 2026-09-11).
 *
 * ⚠️ Vì sao tệp này tồn tại. Toàn bộ bản vá ngôn ngữ thị giác — camera z-up,
 * fit theo hình chiếu, bảng màu theo VAI, thiết diện đi hai lượt — chạy qua
 * suite cũ mà **không một test nào đỏ**. Nghĩa là trước đó không có gì canh
 * phần này: đổi màu, đổi trục lên, đổi cách fit đều lọt. Mỗi `it` dưới đây
 * gắn với một lỗi ĐO ĐƯỢC trên bảy ca P1–P7, không phải một sở thích.
 */
import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import * as THREE from "three";
import {
  khungNhinVua, huongNhin, phuongViCuaPhapTuyen, PHUONG_VI_DO, DO_CAO_DO,
  type HopBao,
} from "./scene3d-camera";
import { buildObject3D, matCatBet } from "./scene3d-view";
import { BE_DAY_PX, capNhatDoPhanGiai } from "./scene3d-wide-line";
import type { SceneObject } from "./scene3d-model";

const FOV = 50;
const TI_LE = 16 / 9;

/** Gom mọi con cháu thành danh sách phẳng. */
function gom(o: THREE.Object3D): THREE.Object3D[] {
  const ra: THREE.Object3D[] = [];
  o.traverse((c) => ra.push(c));
  return ra;
}

/** Phần khung mà hộp bao chiếm, đo ĐỘC LẬP với hàm đang kiểm. */
function doPhu(hop: { min: number[]; max: number[] },
  viTri: number[], nhinVao: number[], len: number[]): number {
  const cam = new THREE.PerspectiveCamera(FOV, TI_LE, 0.1, 1e4);
  cam.up.set(len[0], len[1], len[2]);
  cam.position.set(viTri[0], viTri[1], viTri[2]);
  cam.lookAt(nhinVao[0], nhinVao[1], nhinVao[2]);
  cam.updateMatrixWorld(true);
  cam.updateProjectionMatrix();
  let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
  for (const x of [hop.min[0], hop.max[0]]) {
    for (const y of [hop.min[1], hop.max[1]]) {
      for (const z of [hop.min[2], hop.max[2]]) {
        const p = new THREE.Vector3(x, y, z).project(cam);
        x0 = Math.min(x0, p.x); x1 = Math.max(x1, p.x);
        y0 = Math.min(y0, p.y); y1 = Math.max(y1, p.y);
      }
    }
  }
  return Math.max((x1 - x0) / 2, (y1 - y0) / 2);
}

describe("camera — trục lên và cách fit", () => {
  it("`up` là trục z CỦA HÌNH HỌC, không phải y của three.js", () => {
    // Toạ độ bài toán dùng z làm chiều cao (S(0;0;6), trụ O→K theo z). Với
    // `up = (0,1,0)` thì mọi khối NẰM NGHIÊNG — khối chóp p1 đọc ra một tứ
    // giác dẹt. Đo trên bảy ca: camera cũ 0/7 đạt, camera này 7/7.
    const kn = khungNhinVua({ min: [-1, -1, -1], max: [1, 1, 1] }, FOV, TI_LE)!;
    expect(kn.huongLen).toEqual([0, 0, 1]);
  });

  it("fit theo HÌNH CHIẾU, không theo cầu ngoại tiếp", () => {
    // Cầu ngoại tiếp lớn hơn hình: nó lấp 68 % khung thì hình thật chỉ lấp
    // 0,68/√3 ≈ 39 %. Phép kiểm: với một phiến MỎNG, khoảng cách theo lối cũ
    // (bán kính cầu ngoại tiếp / sin(fov/2) / 0,68) phải XA HƠN hẳn bản này.
    const hop: HopBao = { min: [-10, -10, -0.1], max: [10, 10, 0.1] };
    const kn = khungNhinVua(hop, FOV, TI_LE)!;
    const tam = [0, 0, 0];
    const khoangMoi = Math.hypot(...kn.viTri.map((v, i) => v - tam[i]));

    const nua = [10, 10, 0.1];
    const banKinh = Math.hypot(...nua);
    const fov = (FOV * Math.PI) / 180;
    const fovNgang = 2 * Math.atan(Math.tan(fov / 2) * TI_LE);
    const khoangCu = Math.max(banKinh / Math.sin(fov / 2),
      banKinh / Math.sin(fovNgang / 2)) / 0.68;

    expect(khoangMoi).toBeLessThan(khoangCu);
  });

  it("hình chiếm khoảng 66 % chiều bị bó — đo bằng camera three.js thật", () => {
    const bo: HopBao[] = [
      { min: [-1, -1, -1], max: [1, 1, 1] },
      { min: [-10, -10, -0.1], max: [10, 10, 0.1] },   // phiến mỏng
      { min: [0, 0, 0], max: [5, 5, 24] },              // cột cao, như hình trụ p6
    ];
    for (const hop of bo) {
      const kn = khungNhinVua(hop, FOV, TI_LE)!;
      const phu = doPhu(hop, kn.viTri, kn.nhinVao, kn.huongLen);
      expect(phu).toBeGreaterThan(0.6);
      expect(phu).toBeLessThan(0.72);
    }
  });

  it("hộp to hơn ⇒ camera lùi xa hơn (bất biến cũ, giữ nguyên)", () => {
    const gan = khungNhinVua({ min: [-1, -1, -1], max: [1, 1, 1] }, FOV, TI_LE)!;
    const xa = khungNhinVua({ min: [-10, -10, -10], max: [10, 10, 10] }, FOV, TI_LE)!;
    expect(Math.hypot(...xa.viTri)).toBeGreaterThan(Math.hypot(...gan.viTri));
  });

  it("đầu vào hỏng ⇒ null, không bao giờ NaN (bất biến cũ, giữ nguyên)", () => {
    expect(khungNhinVua(null, FOV, 1)).toBeNull();
    expect(khungNhinVua({ min: [0, 0, 0], max: [1, 1, 1] }, 0, 1)).toBeNull();
    expect(khungNhinVua({ min: [0, 0, 0], max: [1, 1, 1] }, FOV, 0)).toBeNull();
    expect(khungNhinVua({ min: [0, 0, 0], max: [1, 1, 1] }, FOV, 1, Number.NaN)).toBeNull();
    const mot = khungNhinVua({ min: [1, 1, 1], max: [1, 1, 1] }, FOV, TI_LE)!;
    for (const v of [...mot.viTri, ...mot.nhinVao]) expect(Number.isFinite(v)).toBe(true);
  });

  it("guard phương vị: ghi đè góc thì camera ĐỔI CHỖ", () => {
    // Guard thiết diện bẹp truyền một phương vị khác vào. Nếu tham số ấy bị
    // bỏ qua thì guard là mã chết — đây là phép kiểm chống đúng chuyện đó.
    const hop: HopBao = { min: [-1, -1, -1], max: [1, 1, 1] };
    const mac = khungNhinVua(hop, FOV, TI_LE)!;
    const doi = khungNhinVua(hop, FOV, TI_LE, PHUONG_VI_DO + 90)!;
    const lech = Math.hypot(...mac.viTri.map((v, i) => v - doi.viTri[i]));
    expect(lech).toBeGreaterThan(0.5);
  });

  it("guard nhận ra mặt cắt BẸP bằng phép so BA CHIỀU, không bằng hiệu phương vị", () => {
    // Ca tổng hợp đã bác bản đầu của guard. Hướng nhìn mặc định:
    const d = huongNhin(PHUONG_VI_DO, DO_CAO_DO);
    // Pháp tuyến ⟂ hướng nhìn ⇒ hướng nhìn NẰM TRONG mặt cắt ⇒ thiết diện
    // chiếu ra một ĐOẠN THẲNG (đo trên bộ dựng mockup: tỉ lệ trục = 0).
    const n: [number, number, number] = [-d[2] / d[0], 0, 1];
    expect(Math.abs(d[0] * n[0] + d[1] * n[1] + d[2] * n[2])).toBeLessThan(1e-12);
    expect(matCatBet(n, PHUONG_VI_DO)).toBe(true);

    // ⚠️ Chính ca này có hiệu PHƯƠNG VỊ là 125°, cách 90° tới 35°. Bản guard
    // đầu tiên so hiệu phương vị với 90° nên đã bỏ lọt nó. Phép kiểm dưới đây
    // giữ cho lối so ấy không quay lại.
    const goc = phuongViCuaPhapTuyen(n)!;
    const hieuPhuongVi = Math.abs((((PHUONG_VI_DO - goc) % 360) + 540) % 360 - 180);
    expect(Math.abs(hieuPhuongVi - 90)).toBeGreaterThan(30);

    // Và bảy ca thật KHÔNG được nổ guard — pháp tuyến của chúng cách xa mặt bẹp.
    for (const nt of [[2, 0, -1], [1, 0, 1], [0, 0, 1]] as [number, number, number][]) {
      expect(matCatBet(nt, PHUONG_VI_DO)).toBe(false);
    }
  });

  it("phương vị của pháp tuyến: thẳng đứng ⇒ null, không phải 0", () => {
    // Pháp tuyến (0;0;1) không có phương vị. Trả 0 thay vì null sẽ khiến guard
    // xoay camera theo một góc bịa ra.
    expect(phuongViCuaPhapTuyen([0, 0, 1])).toBeNull();
    expect(phuongViCuaPhapTuyen([1, 0, 0])).toBeCloseTo(0, 6);
    expect(phuongViCuaPhapTuyen([0, 1, 0])).toBeCloseTo(90, 6);
    const h = huongNhin(PHUONG_VI_DO, DO_CAO_DO);
    expect(Math.hypot(h[0], h[1], h[2])).toBeCloseTo(1, 9);
    expect(h[2]).toBeGreaterThan(0);          // nhìn từ TRÊN xuống
  });
});

const KHOI: SceneObject = {
  id: "K", label: "Khối", type: "solid", render: "mesh",
  origin: "derived", producer: "construct_solid", depends: [],
  vertices: [["0", "0", "0"], ["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
  faces: [[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]],
};

describe("bảng màu — mỗi màu MỘT vai", () => {
  const mau = (o: THREE.Object3D): number | null => {
    const m = (o as THREE.Mesh).material as THREE.Material | undefined;
    return m && "color" in m ? (m as THREE.MeshBasicMaterial).color.getHex() : null;
  };

  it("cạnh khuất KHÁC màu cạnh thấy — khuất là một vai, không phải bản mờ", () => {
    const con = gom(buildObject3D(KHOI, false)!);
    const thay = con.find((c) => c.name === "canh:K:thay")!;
    const khuat = con.find((c) => c.name === "canh:K:khuat")!;
    expect(mau(thay)).not.toBeNull();
    expect(mau(khuat)).not.toBe(mau(thay));
  });

  it("điểm chỉ có MỘT màu — nguồn gốc vật không phải thông tin của người học", () => {
    const lam = (origin: "free" | "derived"): number => {
      const d: SceneObject = {
        id: `P-${origin}`, label: "P", type: "point3", render: "point_marker",
        origin, producer: null, depends: [], xyz: ["0", "0", "0"],
      };
      const con = gom(buildObject3D(d, false)!);
      const m = con.map(mau).find((x) => x !== null);
      return m as number;
    };
    expect(lam("free")).toBe(lam("derived"));
  });

  it("thiết diện đa giác đi HAI LƯỢT: phần bị khối che phải đọc ra là khuất", () => {
    // Bản trước vẽ nó bằng một `THREE.Line` liền, nên cạnh sau của thiết diện
    // `p1` hiện y hệt cạnh trước — hình mất đúng câu trả lời "trước hay sau".
    const td: SceneObject = {
      id: "T", label: "Thiết diện", type: "section", render: "polygon",
      origin: "derived", producer: "construct_section", depends: [],
      polygon: [["0", "0", "1"], ["1", "0", "1"], ["1", "1", "1"]], closed: true,
    };
    const con = gom(buildObject3D(td, false)!);
    const thay = con.find((c) => c.name.endsWith(":thay"));
    const khuat = con.find((c) => c.name.endsWith(":khuat"));
    expect(thay).toBeDefined();
    expect(khuat).toBeDefined();
    expect(((thay as THREE.Line).material as THREE.Material).depthFunc)
      .toBe(THREE.LessEqualDepth);
    expect(((khuat as THREE.Line).material as THREE.Material).depthFunc)
      .toBe(THREE.GreaterDepth);
    // Hai phần CÙNG màu: chúng là một vật, chỉ khác trạng thái nhìn thấy.
    expect(mau(khuat!)).toBe(mau(thay!));
  });

  it("mặt khối trong suốt — không đặc tới mức nuốt đường bên trong", () => {
    const con = gom(buildObject3D(KHOI, false)!);
    const mesh = con.find((c) => (c as THREE.Mesh).isMesh
      && !(c.userData?.chieuSau)) as THREE.Mesh;
    const m = mesh.material as THREE.MeshStandardMaterial;
    expect(m.transparent).toBe(true);
    expect(m.opacity).toBeLessThanOrEqual(0.1);
  });
});

/* ──────────────────────────────────────────────────────────────────────────
 * VAI NGỮ NGHĨA ≠ TRẠNG THÁI CHỌN
 *
 * Lỗi đã đo trên sản phẩm thật (`af.mp4`, p1): mặt phẳng (α) và ba trong năm
 * điểm hiện **màu xanh chọn** dù người học chưa bấm vào đâu. Nguồn: nơi gọi
 * `buildObject3D` rơi về `highlightedAt(scene, buoc)` — tập vật *vừa dựng ở
 * bước này* — khi không có `selected_id`, rồi tô cả tập ấy bằng `MAU.highlight`.
 * Ngôn ngữ thị giác đã duyệt không có kênh màu nào cho "vừa dựng".
 * ────────────────────────────────────────────────────────────────────────── */
describe("vai ngữ nghĩa ≠ trạng thái chọn", () => {
  const HIGHLIGHT = 0x0075de;
  const SECTION = 0xd95a43;
  const SURFACE = 0x77736f;

  const mauCua = (o: THREE.Object3D): number | null => {
    const m = (o as THREE.Mesh).material as THREE.Material | undefined;
    return m && "color" in m ? (m as THREE.MeshBasicMaterial).color.getHex() : null;
  };
  const mauTrong = (o: THREE.Object3D): number[] =>
    gom(o).map(mauCua).filter((x): x is number => x !== null);

  const THIET_DIEN: SceneObject = {
    id: "T", label: "T", type: "section", render: "polygon",
    origin: "derived", producer: "construct_section", depends: [],
    polygon: [["0", "0", "1"], ["1", "0", "1"], ["1", "1", "1"]], closed: true,
  };
  const MAT_PHANG: SceneObject = {
    id: "alpha", label: "(α)", type: "plane3", render: "surface",
    origin: "derived", producer: "construct_plane", depends: [],
    point: ["0", "0", "1"], normal: ["0", "0", "1"],
  };

  it("chưa chọn gì: thiết diện giữ đỏ cam, KHÔNG có màu xanh nào", () => {
    const m = mauTrong(buildObject3D(THIET_DIEN, false)!);
    expect(m).toContain(SECTION);
    expect(m).not.toContain(HIGHLIGHT);
  });

  it("chưa chọn gì: mặt phẳng giữ vai phụ, KHÔNG có màu xanh nào", () => {
    const m = mauTrong(buildObject3D(MAT_PHANG, false)!);
    expect(m).toContain(SURFACE);
    expect(m).not.toContain(HIGHLIGHT);
  });

  it("chưa chọn gì: thân khối trong suốt 0,07 — không phải khối xanh đục", () => {
    const mesh = gom(buildObject3D(KHOI, false)!).find(
      (c) => (c as THREE.Mesh).isMesh && !c.userData?.chieuSau) as THREE.Mesh;
    const m = mesh.material as THREE.MeshStandardMaterial;
    expect(m.opacity).toBeCloseTo(0.07, 5);
    expect(m.color.getHex()).not.toBe(HIGHLIGHT);
  });

  it("nền đỏ: CHỌN thật thì mới bật xanh — cờ vẫn còn tác dụng", () => {
    expect(mauTrong(buildObject3D(THIET_DIEN, true)!)).toContain(HIGHLIGHT);
    expect(mauTrong(buildObject3D(MAT_PHANG, true)!)).toContain(HIGHLIGHT);
  });

  it("renderer chỉ lấy tập nổi bật từ selected_id, không từ bước", () => {
    const nguon = readFileSync(
      join(import.meta.dirname, "scene3d-view.tsx"), "utf-8");
    const i = nguon.indexOf("const daChon = new Set(");
    expect(i, "không thấy tập vật đang chọn").toBeGreaterThan(-1);
    const than = nguon.slice(i, i + 200);
    expect(than).toContain("tuongTac?.selected_id");
    expect(than, "highlightedAt KHÔNG được là nguồn màu")
      .not.toContain("highlightedAt");
  });

  it("thiết diện fill 0,14 và mặt phẳng fill 0,07 — thiết diện nổi hơn", () => {
    const fill = (o: SceneObject): number => {
      const mesh = gom(buildObject3D(o, false)!).find(
        (c) => (c as THREE.Mesh).isMesh && !c.userData?.chieuSau) as THREE.Mesh;
      return (mesh.material as THREE.MeshStandardMaterial).opacity;
    };
    expect(fill(THIET_DIEN)).toBeCloseTo(0.14, 5);
    expect(fill(MAT_PHANG)).toBeCloseTo(0.07, 5);
    expect(fill(THIET_DIEN)).toBeGreaterThan(fill(MAT_PHANG));
  });
});

/* ──────────────────────────────────────────────────────────────────────────
 * BỀ DÀY NÉT THẬT
 *
 * `THREE.LineBasicMaterial.linewidth` bị WebGL bỏ qua: mọi đường vẽ ra đúng
 * 1 px dù khai bao nhiêu. Đo trên ảnh sản phẩm trước bản vá: bề dày trung vị
 * 1,89 px cho MỌI vai; sau bản vá: 3,34 px và có ba bậc phân biệt được.
 * ────────────────────────────────────────────────────────────────────────── */
describe("nét có bề dày thật", () => {
  const netTrong = (o: THREE.Object3D) =>
    gom(o).filter((c) => c.userData?.net === true);
  const vl = (o: THREE.Object3D) =>
    (o as THREE.Mesh).material as unknown as {
      isLineMaterial?: boolean; linewidth: number; worldUnits: boolean;
      dashed: boolean; dashSize: number; gapSize: number;
      resolution: THREE.Vector2; depthFunc: number;
    };

  const THIET_DIEN: SceneObject = {
    id: "T", label: "T", type: "section", render: "polygon",
    origin: "derived", producer: "construct_section", depends: [],
    polygon: [["0", "0", "1"], ["1", "0", "1"], ["1", "1", "1"]], closed: true,
  };

  it("cạnh khối KHÔNG còn dùng LineBasicMaterial", () => {
    const net = netTrong(buildObject3D(KHOI, false)!);
    expect(net.length).toBeGreaterThan(0);
    for (const n of net) expect(vl(n).isLineMaterial).toBe(true);
  });

  it("ba bậc bề dày: thiết diện 3,5 > cạnh thấy 2,8 > cạnh khuất 1,6", () => {
    const canh = netTrong(buildObject3D(KHOI, false)!);
    const thay = canh.find((c) => c.name.endsWith(":thay"))!;
    const khuat = canh.find((c) => c.name.endsWith(":khuat"))!;
    const td = netTrong(buildObject3D(THIET_DIEN, false)!)
      .find((c) => c.name.endsWith(":thay"))!;
    expect(vl(thay).linewidth).toBeCloseTo(BE_DAY_PX.canhThay, 5);
    expect(vl(khuat).linewidth).toBeCloseTo(BE_DAY_PX.canhKhuat, 5);
    expect(vl(td).linewidth).toBeCloseTo(BE_DAY_PX.thietDienThay, 5);
    expect(vl(td).linewidth).toBeGreaterThan(vl(thay).linewidth);
    expect(vl(thay).linewidth).toBeGreaterThan(vl(khuat).linewidth);
  });

  it("bề dày theo MÀN HÌNH — không phình theo khoảng cách camera", () => {
    for (const n of netTrong(buildObject3D(KHOI, false)!)) {
      expect(vl(n).worldUnits).toBe(false);
    }
  });

  it("hai lượt chiều sâu giữ nguyên: thấy LessEqual, khuất Greater + đứt", () => {
    const canh = netTrong(buildObject3D(KHOI, false)!);
    const thay = canh.find((c) => c.name.endsWith(":thay"))!;
    const khuat = canh.find((c) => c.name.endsWith(":khuat"))!;
    expect(vl(thay).depthFunc).toBe(THREE.LessEqualDepth);
    expect(vl(khuat).depthFunc).toBe(THREE.GreaterDepth);
    expect(vl(thay).dashed).toBe(false);
    expect(vl(khuat).dashed).toBe(true);
  });

  it("nét đứt theo tỉ lệ 7/5, không phải 1/1", () => {
    const khuat = netTrong(buildObject3D(KHOI, false)!)
      .find((c) => c.name.endsWith(":khuat"))!;
    expect(vl(khuat).dashSize / vl(khuat).gapSize).toBeCloseTo(7 / 5, 5);
  });

  it("resolution lấy kích thước CSS, cập nhật được khi đổi khung", () => {
    const o = buildObject3D(KHOI, false)!;
    const n = capNhatDoPhanGiai(o, 1440, 900);
    expect(n).toBeGreaterThan(0);
    for (const x of netTrong(o)) {
      expect(vl(x).resolution.x).toBe(1440);
      expect(vl(x).resolution.y).toBe(900);
    }
  });

  it("vật nét mang cờ userData.net — phép quét tam giác loại được nó", () => {
    for (const n of netTrong(buildObject3D(KHOI, false)!)) {
      expect(n.userData.net).toBe(true);
      // và nó ĐÚNG LÀ một Mesh về mặt kiểu — đó là lý do cần cờ.
      expect((n as THREE.Mesh).isMesh).toBe(true);
    }
  });
});
