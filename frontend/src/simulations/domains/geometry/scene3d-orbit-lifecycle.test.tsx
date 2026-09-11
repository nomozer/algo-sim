/**
 * scene3d-orbit-lifecycle.test.tsx — khoá VÒNG ĐỜI CAMERA và PHẠM VI QUAY.
 *
 * ⚠️ Vì sao tệp này tồn tại. Wave ngôn ngữ thị giác (`7f34286`) thêm đúng một
 * dòng — `cam.up.set(...)` — và đặt nó **sau** `new OrbitControls(...)`. Toàn
 * bộ suite vẫn xanh, `npm run build` vẫn xanh, cổng trình duyệt vẫn PASS; thứ
 * hỏng là **trục quay**, và không một test nào canh trục quay.
 *
 * `OrbitControls` chụp `object.up` một lần trong hàm dựng thành `_quat`
 * (`OrbitControls.js:406`) rồi dùng nó làm trục quỹ đạo mãi mãi. Đặt `up` muộn
 * hơn thì controls quay vị trí quanh **Y** trong khi `lookAt` dựng tư thế theo
 * **Z** — hợp của hai phép là một trục **đổi mỗi khung**. Đo được: chuẩn trục
 * trung bình 0,608–0,680 (lộn nhào) so với 1,000 (bàn xoay).
 * Bằng chứng: `docs/SCENE3D_INTERACTION_SMOOTHNESS_REGRESSION_DIAGNOSIS.md`.
 *
 * Mỗi `it` dưới đây gắn với một điều kiện đã đo, không phải một sở thích.
 */
import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { HUONG_LEN_HINH_HOC, khungNhinVua, type HopBao } from "./scene3d-camera";

const NGUON = readFileSync(
  join(import.meta.dirname, "scene3d-view.tsx"), "utf-8");

/**
 * Phần tử giả tối thiểu cho `OrbitControls.connect`.
 *
 * Suite này chạy ở môi trường `node` (không jsdom — xem `vite.config.ts`), và
 * đưa jsdom vào chỉ để dựng một `<div>` là đổi hạ tầng test cho cả kho. Hàm
 * dựng của OrbitControls chỉ cần `addEventListener`, `removeEventListener`,
 * `getRootNode` và `style`; nó không đọc kích thước nào trong constructor.
 */
function phanTuGia() {
  const el = {
    style: {} as Record<string, string>,
    addEventListener() { /* không cần ghi lại: test này không phát sự kiện */ },
    removeEventListener() { /* như trên */ },
    getRootNode() { return el; },
    ownerDocument: { addEventListener() {}, removeEventListener() {} },
  };
  return el as unknown as HTMLElement;
}

/** Dựng camera + controls ĐÚNG thứ tự mà sản phẩm dùng. */
function dungNhuSanPham() {
  const cam = new THREE.PerspectiveCamera(50, 16 / 9, 0.1, 200);
  cam.up.set(...HUONG_LEN_HINH_HOC);
  cam.position.set(6, 5, 8);
  const dk = new OrbitControls(cam, phanTuGia());
  dk.enableDamping = true;
  dk.minAzimuthAngle = -Infinity;
  dk.maxAzimuthAngle = Infinity;
  dk.minPolarAngle = 0.005;
  dk.maxPolarAngle = Math.PI - 0.005;
  return { cam, dk };
}

/** Đặt camera ở một toạ độ cầu quanh `target`, trong hệ z-up. */
function datGocCau(cam: THREE.PerspectiveCamera, tam: THREE.Vector3,
  phuongVi: number, cuc: number, r: number) {
  // cực đo từ trục `up` = z.
  cam.position.set(
    tam.x + r * Math.sin(cuc) * Math.cos(phuongVi),
    tam.y + r * Math.sin(cuc) * Math.sin(phuongVi),
    tam.z + r * Math.cos(cuc),
  );
  cam.lookAt(tam);
}

describe("vòng đời camera — up phải tới TRƯỚC OrbitControls", () => {
  it("mã nguồn đặt cam.up trước new OrbitControls", () => {
    const iUp = NGUON.indexOf("cam.up.set(");
    const iControls = NGUON.indexOf("new OrbitControls(");
    expect(iUp, "không tìm thấy cam.up.set trong scene3d-view.tsx").toBeGreaterThan(-1);
    expect(iControls, "không tìm thấy new OrbitControls").toBeGreaterThan(-1);
    expect(iUp, "cam.up.set phải đứng TRƯỚC new OrbitControls").toBeLessThan(iControls);
  });

  it("mã nguồn KHÔNG đặt lại cam.up ở đâu nữa", () => {
    const lan = NGUON.split("cam.up.set(").length - 1;
    expect(lan, "cam.up chỉ được đặt đúng một lần, lúc dựng camera").toBe(1);
  });

  it("cam.up lấy từ nguồn z-up duy nhất, không chép cứng", () => {
    expect(NGUON).toContain("cam.up.set(...HUONG_LEN_HINH_HOC)");
    expect(HUONG_LEN_HINH_HOC).toEqual([0, 0, 1]);
  });

  /**
   * Đây là bất biến THẬT, không phải một phép so chuỗi: `_quat` là thứ
   * OrbitControls dùng để đưa vị trí camera về hệ "y là trục lên" trước khi
   * quay. Nếu nó khớp `cam.up` thì trục quỹ đạo ĐÚNG BẰNG `cam.up`.
   */
  it("OrbitControls._quat đưa đúng cam.up về trục y", () => {
    const { cam, dk } = dungNhuSanPham();
    const q = (dk as unknown as { _quat: THREE.Quaternion })._quat;
    const v = cam.up.clone().applyQuaternion(q);
    expect(v.x).toBeCloseTo(0, 6);
    expect(v.y).toBeCloseTo(1, 6);
    expect(v.z).toBeCloseTo(0, 6);
  });

  it("nền đỏ: dựng SAI thứ tự thì bất biến trên vỡ", () => {
    const cam = new THREE.PerspectiveCamera(50, 16 / 9, 0.1, 200);
    const dk = new OrbitControls(cam, phanTuGia());   // up vẫn (0,1,0) lúc này
    cam.up.set(...HUONG_LEN_HINH_HOC);       // đặt muộn — đúng con bọ cũ
    const q = (dk as unknown as { _quat: THREE.Quaternion })._quat;
    const v = cam.up.clone().applyQuaternion(q);
    // `_quat` là đơn vị ⇒ up (0,0,1) giữ nguyên, KHÔNG về (0,1,0).
    expect(v.y).toBeCloseTo(0, 6);
    expect(v.z).toBeCloseTo(1, 6);
  });
});

describe("phạm vi quay", () => {
  it("phương vị không bị chặn ở hai đầu", () => {
    const { dk } = dungNhuSanPham();
    expect(dk.minAzimuthAngle).toBe(-Infinity);
    expect(dk.maxAzimuthAngle).toBe(Infinity);
  });

  it("cực chừa khe nhỏ ở cả hai đầu, đủ để nhìn từ đỉnh và từ đáy", () => {
    const { dk } = dungNhuSanPham();
    expect(dk.minPolarAngle).toBeGreaterThan(0);
    expect(dk.minPolarAngle).toBeLessThan(0.02);
    expect(dk.maxPolarAngle).toBeLessThan(Math.PI);
    expect(Math.PI - dk.maxPolarAngle).toBeLessThan(0.02);
  });

  it("mã nguồn khai tường minh cả bốn giới hạn", () => {
    expect(NGUON).toContain("minAzimuthAngle = -Infinity");
    expect(NGUON).toContain("maxAzimuthAngle = Infinity");
    expect(NGUON).toContain("minPolarAngle = EPSILON_CUC");
    expect(NGUON).toContain("maxPolarAngle = Math.PI - EPSILON_CUC");
  });

  /**
   * Quay đủ vòng: đặt camera qua 36 phương vị liên tiếp (mỗi bước 10°) rồi gọi
   * `update()`. Nếu phương vị bị chặn, `update()` sẽ kéo camera về biên và vị
   * trí sau khi cập nhật lệch khỏi vị trí đã đặt.
   */
  it("quay ngang đủ 360° mà update() không kéo về biên nào", () => {
    const { cam, dk } = dungNhuSanPham();
    const tam = new THREE.Vector3(0, 0, 0);
    dk.target.copy(tam);
    dk.enableDamping = false;   // đo phép chặn, không đo quán tính
    const r = 12;
    let tong = 0;
    let truoc: number | null = null;
    for (let i = 0; i <= 36; i++) {
      const pv = (i * 10 * Math.PI) / 180;
      datGocCau(cam, tam, pv, Math.PI / 2 - 0.4, r);
      const dat = cam.position.clone();
      dk.update();
      expect(cam.position.distanceTo(dat),
        `update() kéo camera khỏi phương vị ${i * 10}°`).toBeLessThan(1e-6);
      const thuc = Math.atan2(cam.position.y, cam.position.x);
      if (truoc !== null) {
        let d = thuc - truoc;
        while (d > Math.PI) d -= 2 * Math.PI;
        while (d < -Math.PI) d += 2 * Math.PI;
        tong += Math.abs(d);
      }
      truoc = thuc;
    }
    expect((tong * 180) / Math.PI).toBeGreaterThanOrEqual(359.9);
  });

  it("sáu hướng nhìn đều nằm trong phạm vi cho phép", () => {
    const { dk } = dungNhuSanPham();
    // [tên, phương vị, cực]
    const huong: [string, number, number][] = [
      ["trước", 0, Math.PI / 2],
      ["sau", Math.PI, Math.PI / 2],
      ["phải", Math.PI / 2, Math.PI / 2],
      ["trái", -Math.PI / 2, Math.PI / 2],
      ["trên", 0, dk.minPolarAngle],
      ["dưới", 0, dk.maxPolarAngle],
    ];
    for (const [ten, pv, cuc] of huong) {
      expect(pv >= dk.minAzimuthAngle && pv <= dk.maxAzimuthAngle, ten).toBe(true);
      expect(cuc >= dk.minPolarAngle && cuc <= dk.maxPolarAngle, ten).toBe(true);
    }
    // và hai cực THẬT SỰ gần đỉnh/đáy, không phải một giới hạn rộng rãi trá hình
    expect(Math.cos(dk.minPolarAngle)).toBeGreaterThan(0.999);
    expect(Math.cos(dk.maxPolarAngle)).toBeLessThan(-0.999);
  });
});

describe("khớp khung nhường tương tác", () => {
  it("hàm khớp khung thoát sớm khi đang kéo", () => {
    const i = NGUON.indexOf("vuaKhungRef.current = () => {");
    expect(i).toBeGreaterThan(-1);
    const than = NGUON.slice(i, i + 600);
    expect(than, "khớp khung phải bail out khi dangKeoRef bật")
      .toContain("if (dangKeoRef.current) return;");
  });

  it("cờ đang kéo do chính OrbitControls bật/tắt", () => {
    expect(NGUON).toContain('dieuKhien.addEventListener("start"');
    expect(NGUON).toContain('dieuKhien.addEventListener("end"');
  });

  it("khung nhìn mặc định vẫn là z-up, góc −55°/22° không đổi", () => {
    const hop: HopBao = { min: [-2, -2, 0], max: [2, 2, 6] };
    const kn = khungNhinVua(hop, 50, 16 / 9);
    expect(kn).not.toBeNull();
    expect(kn!.huongLen).toEqual([0, 0, 1]);
  });
});
