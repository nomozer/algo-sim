/**
 * CỔNG NHÂN CHỨNG VUÔNG GÓC (Owner 2026-10-26) — ký hiệu góc vuông chỉ được vẽ khi nhân chứng backend TỰ NHẤT QUÁN
 * với chính cảnh nó nằm trong.
 *
 * Đây không phải suy luận hình học: module này KHÔNG dựng chân, không chọn phương, không trả toạ độ nào — mọi hàm
 * trả `boolean`. Nó đọc lại số backend đã phát và từ chối (fail-closed) khi chúng mâu thuẫn nhau: một dấu vuông góc
 * vẽ từ nhân chứng sai là một mệnh đề sai trước mặt học sinh. Vì thế các phép tích nằm ở ĐÂY, ngoài bốn file
 * trình bày mà `scene3d.test.tsx` cấm tính hình (view/model/annotations/auxiliary).
 */
import type { WitnessShown } from "./scene3d-annotations";
import type { ExactVec3, Scene3D, Vec3 } from "./scene3d-model";
import { toVec3 } from "./scene3d-model";

const tichVo = (a: Vec3, b: Vec3): Vec3 => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const tichVoHuong = (a: Vec3, b: Vec3) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const hieu = (a: Vec3, b: Vec3): Vec3 => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const doDai = (a: Vec3) => Math.hypot(a[0], a[1], a[2]);

/** Sai số TƯƠNG ĐỐI: toạ độ là phân số chính xác hoá float ở biên, nên lệch lớn hơn đây là nhân chứng sai thật. */
export const SAI_SO_NHAN_CHUNG = 1e-6;

/**
 * Điều kiện (sai một ⇒ không vẽ gì, không bao giờ "sửa" cho đúng):
 *   · `u`, `v` khác 0 và vuông góc;  · `v` cùng hướng `from − foot` (dấu neo đúng CHÂN của đoạn vuông góc);
 *   · vật nhận `on` là mặt phẳng ⇒ chân thuộc mặt phẳng, `u` nằm trong nó, `v` song song pháp tuyến;
 *     là đường thẳng ⇒ chân thuộc đường, `u` dọc đường, `v` vuông góc đường;
 *   · có `uTo` ⇒ `uTo − foot` cùng hướng `u` (đoạn chứng minh trùng đúng cạnh của dấu).
 */
export function nhanChungVuongGocHopLe(scene: Pick<Scene3D, "objects">, w: WitnessShown, on?: string): boolean {
  const { from, foot, u, v } = w;
  const nu = doDai(u), nv = doDai(v);
  if (!(nu > 1e-12) || !(nv > 1e-12) || ![...from, ...foot, ...u, ...v].every(Number.isFinite)) return false;
  const eps = SAI_SO_NHAN_CHUNG;
  if (Math.abs(tichVoHuong(u, v)) > eps * nu * nv) return false;
  const doan = hieu(from, foot);
  const nd = doDai(doan);
  const thang = Math.max(1, nd, ...from.map(Math.abs), ...foot.map(Math.abs));
  if (!(nd > eps * thang)) return false;
  if (doDai(tichVo(v, doan)) > eps * nv * nd || tichVoHuong(v, doan) <= 0) return false;
  const vat = on ? scene.objects.find((o) => o.id === on) : undefined;
  if (vat?.type === "plane3" && vat.point && vat.normal) {
    const n = toVec3(vat.normal), nn = doDai(n);
    if (!(nn > 1e-12)) return false;
    if (Math.abs(tichVoHuong(n, hieu(foot, toVec3(vat.point)))) > eps * nn * thang) return false;
    if (Math.abs(tichVoHuong(n, u)) > eps * nn * nu) return false;
    if (doDai(tichVo(n, v)) > eps * nn * nv) return false;
  } else if (vat?.type === "line3" && vat.point && vat.direction) {
    const dd = toVec3(vat.direction), ndd = doDai(dd);
    if (!(ndd > 1e-12)) return false;
    if (doDai(tichVo(dd, hieu(foot, toVec3(vat.point)))) > eps * ndd * thang) return false;
    if (doDai(tichVo(dd, u)) > eps * ndd * nu) return false;
    if (Math.abs(tichVoHuong(dd, v)) > eps * ndd * nv) return false;
  }
  if (w.uTo) {
    const leg = hieu(w.uTo, foot), nl = doDai(leg);
    if (!(nl > eps * thang) || doDai(tichVo(leg, u)) > eps * nl * nu || tichVoHuong(leg, u) <= 0) return false;
  }
  return true;
}

/** Chứng chỉ vuông góc gắn trên một ĐOẠN `[a, b]`: chân là một đầu mút, `from` là đầu kia, và `v` vuông góc mọi
 *  phương mặt phẳng backend chứng nhận (`plane_directions`). */
export function nhanChungDoanHopLe(
  w: { foot: ExactVec3; marker: { u: ExactVec3; v: ExactVec3 }; plane_directions?: ExactVec3[] }, a: Vec3, b: Vec3,
): boolean {
  const chan = toVec3(w.foot);
  const tol = SAI_SO_NHAN_CHUNG * Math.max(1, doDai(hieu(a, b)));
  const tu = doDai(hieu(a, chan)) <= tol ? b : doDai(hieu(b, chan)) <= tol ? a : null;
  if (!tu) return false;
  const v = toVec3(w.marker.v);
  return nhanChungVuongGocHopLe({ objects: [] }, { id: "", vai: "hinh_chieu", from: tu, foot: chan,
    u: toVec3(w.marker.u), v })
    && (w.plane_directions ?? []).every((d) => {
      const p = toVec3(d);
      return Math.abs(tichVoHuong(p, v)) <= SAI_SO_NHAN_CHUNG * doDai(p) * doDai(v);
    });
}

/** `[p, q]` nằm TRỌN trên một đoạn đã vẽ (cùng đường, trong khoảng hai đầu mút) — để đoạn chứng minh không chồng nét. */
export function namTrenDoanDaVe(p: Vec3, q: Vec3, doan: readonly [Vec3, Vec3][]): boolean {
  return doan.some(([a, b]) => {
    const ab = hieu(b, a), l2 = tichVoHuong(ab, ab);
    if (!(l2 > 1e-18)) return false;
    const tol = SAI_SO_NHAN_CHUNG * Math.sqrt(l2);
    return [p, q].every((x) => {
      const t = tichVoHuong(hieu(x, a), ab) / l2;
      const r = hieu(x, [a[0] + t * ab[0], a[1] + t * ab[1], a[2] + t * ab[2]]);
      return t >= -1e-9 && t <= 1 + 1e-9 && doDai(r) <= tol;
    });
  });
}
