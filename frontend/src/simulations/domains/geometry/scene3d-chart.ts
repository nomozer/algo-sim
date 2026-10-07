/**
 * KHUNG → KHÔNG GIAN (exact-dimensions).
 *
 * Toạ độ cảnh là toạ độ của KHUNG affine mà chương trình đặt; độ dài thật đo bằng metric khung G (backend
 * `geometry/metric.py`, phát ở `scene.chart_metric` CHỈ khi khác đồng nhất). Renderer cần hình Euclid thật, nên MỘT lần
 * khi nhận cảnh, mọi toạ độ đi qua T (Cholesky: Tᵀ·T = G): điểm và phương ↦ T·p, pháp tuyến mặt phẳng (covector) ↦
 * T⁻ᵀ·n. Phép affine giữ thuộc, tỉ số, giao — nên `edge_span`, thứ tự đỉnh và khoá toạ độ (`scene3d-subentities`) vẫn
 * đúng; T là hàm của TỪNG toạ độ nên cùng một điểm khung luôn ra cùng một chuỗi.
 *
 * Đây là BIÊN HIỂN THỊ: số thế giới làm tròn 1e-9 thành chuỗi phân số (`toNumber` giữ nguyên luật). Không phép tính,
 * phép so hay đáp số nào đọc chúng — backend đã tính mọi đại lượng chính xác trong khung.
 */
import type { Exact, ExactVec3, Scene3D, SceneObject } from "./scene3d-model";
import { toNumber, toVec3 } from "./scene3d-model";

type M3 = [[number, number, number], [number, number, number], [number, number, number]];

/** T (tam giác trên, Tᵀ·T = G) của cảnh có metric khung; `null` ⇒ khung Euclid (mọi họ khác). */
export function maTranKhung(scene: Pick<Scene3D, "chart_metric">): M3 | null {
  const g = scene.chart_metric;
  if (!g) return null;
  const G = g.map((r) => r.map(toNumber));
  const l00 = Math.sqrt(G[0][0]);
  const l10 = G[1][0] / l00;
  const l20 = G[2][0] / l00;
  const l11 = Math.sqrt(G[1][1] - l10 * l10);
  const l21 = (G[2][1] - l20 * l10) / l11;
  const l22 = Math.sqrt(G[2][2] - l20 * l20 - l21 * l21);
  // L tam giác dưới (G = L·Lᵀ) ⇒ T = Lᵀ.
  return [[l00, l10, l20], [0, l11, l21], [0, 0, l22]];
}

const nhan = (m: M3, v: [number, number, number]): [number, number, number] =>
  [0, 1, 2].map((i) => m[i][0] * v[0] + m[i][1] * v[1] + m[i][2] * v[2]) as [number, number, number];

/** T⁻ᵀ cho pháp tuyến (T tam giác trên ⇒ nghịch đảo trực tiếp). */
function nghichChuyenVi(t: M3): M3 {
  const [[a, b, c], [, d, e], [, , f]] = t;
  const inv: M3 = [[1 / a, -b / (a * d), (b * e - c * d) / (a * d * f)], [0, 1 / d, -e / (d * f)], [0, 0, 1 / f]];
  return [[inv[0][0], inv[1][0], inv[2][0]], [inv[0][1], inv[1][1], inv[2][1]], [inv[0][2], inv[1][2], inv[2][2]]];
}

const xau = (x: number): Exact => `${Math.round(x * 1e9)}/1000000000`;

/** Cảnh với toạ độ THẾ GIỚI — chính `scene` khi không có metric khung (không sao chép, không đổi một byte). */
export function veKhongGian(scene: Scene3D): Scene3D {
  const t = maTranKhung(scene);
  if (!t) return scene;
  const tn = nghichChuyenVi(t);
  const d = (v: ExactVec3): ExactVec3 => nhan(t, toVec3(v)).map(xau) as ExactVec3;
  const n = (v: ExactVec3): ExactVec3 => nhan(tn, toVec3(v)).map(xau) as ExactVec3;
  const ds = (vs?: ExactVec3[]) => vs?.map(d);
  const vat = (o: SceneObject): SceneObject => {
    const r: SceneObject = { ...o };
    for (const k of ["xyz", "point", "point_a", "point_b", "anchor", "rim_point", "center", "direction", "major_dir",
      "minor_dir"] as const) {
      if (o[k]) r[k] = d(o[k] as ExactVec3);
    }
    if (o.apex_or_top) r.apex_or_top = d(o.apex_or_top);
    if (o.normal) r.normal = n(o.normal);
    if (o.endpoints) r.endpoints = ds(o.endpoints);
    if (o.vertices) r.vertices = ds(o.vertices);
    if (o.polygon) r.polygon = ds(o.polygon);
    if (o.steps) r.steps = o.steps.map((s) => ({ ...s, a: d(s.a), b: d(s.b) }));
    const w = o.annotation?.witness;
    if (w && o.annotation) {
      r.annotation = { ...o.annotation, witness: { ...w, foot: d(w.foot), marker: { u: d(w.marker.u), v: d(w.marker.v) } } };
    }
    return r;
  };
  return { ...scene, objects: scene.objects.map(vat) };
}

/** T dưới dạng ma trận 4×4 cột-chính (cho ảnh chụp camera của bộ đo: model = xoay hiển thị · T). */
export function maTranKhung4(scene: Pick<Scene3D, "chart_metric">): number[] | null {
  const t = maTranKhung(scene);
  if (!t) return null;
  return [t[0][0], t[1][0], t[2][0], 0, t[0][1], t[1][1], t[2][1], 0, t[0][2], t[1][2], t[2][2], 0, 0, 0, 0, 1];
}
