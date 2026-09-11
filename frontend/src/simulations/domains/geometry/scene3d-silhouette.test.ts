/**
 * scene3d-silhouette.test.ts — khoá TOÁN của đường bao khối cong.
 *
 * ⚠️ Vì sao tệp này tồn tại. Đường bao là thứ DUY NHẤT làm nên hình dáng của
 * mặt trơn: bỏ nó thì p4/p5 dựng ra một vệt xám không một nét nào — đúng trạng
 * thái đo được trên sản phẩm trước wave này. Nhưng nó cũng là thứ dễ "trông
 * như đúng": vẽ hai đường thẳng bất kỳ hai bên hình trụ thì ảnh tĩnh ở góc mặc
 * định vẫn hợp lý, và chỉ sai khi xoay. Nên mỗi `it` dưới đây kiểm một TÍNH
 * CHẤT HÌNH HỌC kiểm được độc lập, không so với một ảnh mẫu.
 */
import { describe, expect, it } from "vitest";
import * as THREE from "three";
import { duongBaoKhoiCong, type KhoiCongMoTa } from "./scene3d-silhouette";

const MAU = { thay: 0x1f1f1f, khuat: 0x7d7975 };

/** Mọi đầu mút của các đoạn trong một vật nét. */
function dauMut(d: THREE.Object3D): THREE.Vector3[] {
  const g = (d as THREE.Mesh).geometry as THREE.BufferGeometry;
  const at = g.getAttribute("instanceStart") as THREE.InterleavedBufferAttribute;
  const a = at.data.array as Float32Array;
  const ra: THREE.Vector3[] = [];
  for (let i = 0; i + 5 < a.length; i += 6) {
    ra.push(new THREE.Vector3(a[i], a[i + 1], a[i + 2]));
    ra.push(new THREE.Vector3(a[i + 3], a[i + 4], a[i + 5]));
  }
  return ra;
}

function timBao(bao: { nhom: THREE.Group }, khop: string): THREE.Object3D {
  let ra: THREE.Object3D | null = null;
  bao.nhom.traverse((c) => { if (c.name.includes(khop)) ra = c; });
  if (!ra) throw new Error(`không thấy vật nét khớp "${khop}"`);
  return ra;
}

const TRU: KhoiCongMoTa = {
  kind: "cylinder",
  tam: new THREE.Vector3(0, 0, 0),
  dinh: new THREE.Vector3(0, 0, 10),
  r: 6, h: 10,
};
const NON: KhoiCongMoTa = {
  kind: "cone",
  tam: new THREE.Vector3(0, 0, 0),
  dinh: new THREE.Vector3(0, 0, 9),
  r: 4, h: 9,
};
const CAU: KhoiCongMoTa = {
  kind: "ball",
  tam: new THREE.Vector3(1, 2, 3), dinh: null, r: 5, h: 0,
};

describe("hình trụ", () => {
  it("có hai vành và hai đường sinh bao", () => {
    const bao = duongBaoKhoiCong(TRU, MAU, 0.3, "tru")!;
    expect(bao).not.toBeNull();
    const ten: string[] = [];
    bao.nhom.traverse((c) => { if (c.name) ten.push(c.name); });
    expect(ten.some((x) => x.startsWith("vanh-day:"))).toBe(true);
    expect(ten.some((x) => x.startsWith("vanh-tren:"))).toBe(true);
    expect(ten.some((x) => x.startsWith("bao:"))).toBe(true);
  });

  it("vành đi HAI LƯỢT chiều sâu — phần bị khối che đọc ra là khuất", () => {
    const bao = duongBaoKhoiCong(TRU, MAU, 0.3, "tru")!;
    const thay = timBao(bao, "vanh-day:tru:thay") as THREE.Mesh;
    const khuat = timBao(bao, "vanh-day:tru:khuat") as THREE.Mesh;
    expect((thay.material as THREE.Material).depthFunc).toBe(THREE.LessEqualDepth);
    expect((khuat.material as THREE.Material).depthFunc).toBe(THREE.GreaterDepth);
  });

  /**
   * Tính chất định nghĩa của đường sinh bao: mặt tiếp tuyến dọc nó CHỨA MẮT.
   * Với trụ, pháp tuyến mặt ấy là hướng bán kính `n`, nên `n·(C − P) = 0`.
   */
  it("đường sinh bao thoả đúng điều kiện tiếp tuyến n·(C−P) = 0", () => {
    const bao = duongBaoKhoiCong(TRU, MAU, 0.3, "tru")!;
    for (const cam of [new THREE.Vector3(30, -20, 14), new THREE.Vector3(-40, 5, 2),
      new THREE.Vector3(0, 25, 60)]) {
      bao.capNhat(cam);
      const mut = dauMut(timBao(bao, "bao:tru"));
      expect(mut.length).toBe(4);
      for (const p of mut) {
        const n = new THREE.Vector3(p.x, p.y, 0).normalize();  // trục là z
        expect(Math.hypot(p.x, p.y)).toBeCloseTo(TRU.r, 4);    // nằm trên mặt trụ
        const v = cam.clone().sub(p);
        expect(Math.abs(n.dot(v))).toBeLessThan(1e-3);
      }
    }
  });

  it("hai đường sinh song song trục và trải hết chiều cao", () => {
    const bao = duongBaoKhoiCong(TRU, MAU, 0.3, "tru")!;
    bao.capNhat(new THREE.Vector3(30, -20, 14));
    const mut = dauMut(timBao(bao, "bao:tru"));
    for (let i = 0; i < mut.length; i += 2) {
      expect(mut[i].z).toBeCloseTo(0, 6);
      expect(mut[i + 1].z).toBeCloseTo(10, 6);
      expect(Math.hypot(mut[i].x - mut[i + 1].x, mut[i].y - mut[i + 1].y))
        .toBeCloseTo(0, 6);
    }
  });

  it("xoay camera ⇒ đường sinh ĐỔI CHỖ (không phải hai đường cố định)", () => {
    const bao = duongBaoKhoiCong(TRU, MAU, 0.3, "tru")!;
    bao.capNhat(new THREE.Vector3(30, 0, 5));
    const a = dauMut(timBao(bao, "bao:tru")).map((p) => p.clone());
    bao.capNhat(new THREE.Vector3(0, 30, 5));
    const b = dauMut(timBao(bao, "bao:tru"));
    const lech = Math.max(...a.map((p, i) => p.distanceTo(b[i])));
    expect(lech).toBeGreaterThan(1);
  });

  it("cập nhật KHÔNG cấp phát lại bộ đệm — cùng một mảng", () => {
    const bao = duongBaoKhoiCong(TRU, MAU, 0.3, "tru")!;
    const d = timBao(bao, "bao:tru") as THREE.Mesh;
    const g = d.geometry as THREE.BufferGeometry;
    const truoc = (g.getAttribute("instanceStart") as THREE.InterleavedBufferAttribute).data.array;
    bao.capNhat(new THREE.Vector3(30, -20, 14));
    bao.capNhat(new THREE.Vector3(-10, 40, 3));
    const sau = (g.getAttribute("instanceStart") as THREE.InterleavedBufferAttribute).data.array;
    expect(sau).toBe(truoc);
  });
});

describe("hình nón", () => {
  it("hai đường sinh bao đều đi qua ĐỈNH và chạm vành đáy", () => {
    const bao = duongBaoKhoiCong(NON, MAU, 0.3, "non")!;
    bao.capNhat(new THREE.Vector3(25, -18, 12));
    const mut = dauMut(timBao(bao, "bao:non"));
    expect(mut.length).toBe(4);
    for (let i = 0; i < mut.length; i += 2) {
      expect(Math.hypot(mut[i].x, mut[i].y)).toBeCloseTo(NON.r, 4);
      expect(mut[i].z).toBeCloseTo(0, 6);
      expect(mut[i + 1].distanceTo(NON.dinh!)).toBeCloseTo(0, 6);
    }
  });

  /** Pháp tuyến mặt tiếp tuyến của nón dọc đường sinh qua `P` là `h·n + r·u`. */
  it("đường sinh bao thoả điều kiện tiếp tuyến của NÓN", () => {
    const bao = duongBaoKhoiCong(NON, MAU, 0.3, "non")!;
    for (const cam of [new THREE.Vector3(25, -18, 12), new THREE.Vector3(-30, 8, 20)]) {
      bao.capNhat(cam);
      const mut = dauMut(timBao(bao, "bao:non"));
      for (let i = 0; i < mut.length; i += 2) {
        const p = mut[i];
        const n = new THREE.Vector3(p.x, p.y, 0).normalize();
        const m = new THREE.Vector3(
          NON.h * n.x, NON.h * n.y, NON.h * n.z + NON.r);       // h·n + r·u, u = z
        const v = cam.clone().sub(p);
        expect(Math.abs(m.dot(v)) / m.length() / v.length()).toBeLessThan(1e-4);
      }
    }
  });

  it("nón KHÔNG có vành trên", () => {
    const bao = duongBaoKhoiCong(NON, MAU, 0.3, "non")!;
    const ten: string[] = [];
    bao.nhom.traverse((c) => { if (c.name) ten.push(c.name); });
    expect(ten.some((x) => x.startsWith("vanh-tren:"))).toBe(false);
    expect(ten.some((x) => x.startsWith("vanh-day:"))).toBe(true);
  });
});

describe("mặt cầu", () => {
  it("đường bao là đường tròn tiếp xúc, mọi điểm cách đều mắt", () => {
    const bao = duongBaoKhoiCong(CAU, MAU, 0.3, "cau")!;
    const cam = new THREE.Vector3(20, -15, 30);
    bao.capNhat(cam);
    const mut = dauMut(timBao(bao, "bao:cau"));
    // 48 cung ⇒ 96 đầu mút. Con số cụ thể là quyết định TRÌNH BÀY
    // (`VONG_CHIA_BAO`); ở đây chỉ cần đủ dày để gọi là một đường tròn.
    expect(mut.length).toBeGreaterThanOrEqual(64);
    const kc = mut.map((p) => p.distanceTo(cam));
    expect(Math.max(...kc) - Math.min(...kc)).toBeLessThan(1e-3);
    // và mọi điểm nằm ĐÚNG trên mặt cầu
    for (const p of mut) expect(p.distanceTo(CAU.tam)).toBeCloseTo(CAU.r, 3);
  });

  it("bán kính bao NHỎ hơn bán kính cầu, và tiến tới nó khi lùi xa", () => {
    const bao = duongBaoKhoiCong(CAU, MAU, 0.3, "cau")!;
    const banKinhBao = (D: number) => {
      bao.capNhat(new THREE.Vector3(CAU.tam.x + D, CAU.tam.y, CAU.tam.z));
      const mut = dauMut(timBao(bao, "bao:cau"));
      const tb = new THREE.Vector3();
      for (const p of mut) tb.add(p);
      tb.divideScalar(mut.length);
      return mut.reduce((s, p) => s + p.distanceTo(tb), 0) / mut.length;
    };
    const gan = banKinhBao(8), xa = banKinhBao(500);
    expect(gan).toBeLessThan(CAU.r);
    expect(xa).toBeGreaterThan(gan);
    expect(xa).toBeCloseTo(CAU.r, 1);
  });

  it("camera TRONG lòng cầu ⇒ không đổi gì, không NaN", () => {
    const bao = duongBaoKhoiCong(CAU, MAU, 0.3, "cau")!;
    bao.capNhat(new THREE.Vector3(20, -15, 30));
    const truoc = dauMut(timBao(bao, "bao:cau")).map((p) => p.clone());
    bao.capNhat(CAU.tam.clone());                       // D = 0 < r
    const sau = dauMut(timBao(bao, "bao:cau"));
    for (let i = 0; i < sau.length; i++) {
      expect(Number.isFinite(sau[i].x)).toBe(true);
      expect(sau[i].distanceTo(truoc[i])).toBeCloseTo(0, 6);
    }
  });
});

describe("đầu vào hỏng", () => {
  it("bán kính 0 ⇒ null; trụ/nón thiếu đỉnh ⇒ null", () => {
    expect(duongBaoKhoiCong({ ...TRU, r: 0 }, MAU, 0.3, "x")).toBeNull();
    expect(duongBaoKhoiCong({ ...TRU, dinh: null }, MAU, 0.3, "x")).toBeNull();
    expect(duongBaoKhoiCong({ ...NON, h: 0 }, MAU, 0.3, "x")).toBeNull();
  });

  it("nhìn DỌC TRỤC hình trụ ⇒ không bịa đường sinh, không NaN", () => {
    const bao = duongBaoKhoiCong(TRU, MAU, 0.3, "tru")!;
    bao.capNhat(new THREE.Vector3(0, 0, 100));   // R ≈ 0
    for (const p of dauMut(timBao(bao, "bao:tru"))) {
      expect(Number.isFinite(p.x) && Number.isFinite(p.y) && Number.isFinite(p.z))
        .toBe(true);
    }
  });
});
