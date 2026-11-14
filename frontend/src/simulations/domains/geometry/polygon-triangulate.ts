/**
 * Chia tam giác một đa giác PHẲNG ĐƠN trong không gian — kể cả LÕM.
 *
 * ─── VÌ SAO KHÔNG DÙNG QUẠT TAM GIÁC ────────────────────────────────────
 *
 * Quạt từ đỉnh 0 chỉ đúng khi đa giác LỒI. Với đa giác lõm, một tam giác của
 * quạt trùm ra ngoài biên và **lấp mất phần lõm** — hình vẽ ra trông hợp lý
 * mà sai, đúng lớp lỗi mà `NONCONVEX_POLYHEDRON_VOLUME_FOUNDATION` vừa sửa ở
 * tầng thể tích. Đo được trên đáy `A(0,0,0) B(4,0,0) C(4,4,0) D(2,1,0)
 * E(0,4,0)`: diện tích thật `10`, quạt phủ `14`.
 *
 * Sửa thể tích mà để renderer lấp phần lõm là chữa nửa bệnh: con số đúng, còn
 * thứ học sinh NHÌN THẤY vẫn sai.
 *
 * ─── NÓ KHÔNG PHẢI MỘT THẨM QUYỀN HÌNH HỌC THỨ HAI ──────────────────────
 *
 * Nó không quyết định gì về hình: thứ tự đỉnh quanh mặt do kernel quyết, và
 * hàm này chỉ **nối** chúng lại. Nó không sinh đỉnh mới — mọi tam giác trả về
 * là ba CHỈ SỐ vào chính mảng đầu vào, nên không có toạ độ nào do frontend
 * bịa ra.
 */

export type Diem3 = readonly [number, number, number];

/** Trục toạ độ 2D cục bộ trực chuẩn (orthonormal) của mặt phẳng chứa đa giác. */
function heTrucCucBo(pts: readonly Diem3[]): [Diem3, Diem3] | null {
  const [a] = pts;
  let maxSpan = 0;
  let uIdx = -1;
  let uLen = 0;
  for (let i = 1; i < pts.length; i += 1) {
    const d: Diem3 = [pts[i][0] - a[0], pts[i][1] - a[1], pts[i][2] - a[2]];
    const len = Math.hypot(d[0], d[1], d[2]);
    if (len > maxSpan) {
      maxSpan = len;
      uIdx = i;
      uLen = len;
    }
  }
  if (uIdx < 0 || maxSpan <= 0 || !Number.isFinite(maxSpan)) return null;
  const uRaw: Diem3 = [
    (pts[uIdx][0] - a[0]) / uLen,
    (pts[uIdx][1] - a[1]) / uLen,
    (pts[uIdx][2] - a[2]) / uLen,
  ];
  // Pháp tuyến = tổng tích có hướng quanh biên (bền hơn "ba đỉnh đầu", vì ba
  // đỉnh đầu có thể thẳng hàng).
  let n: Diem3 = [0, 0, 0];
  for (let i = 0; i < pts.length; i += 1) {
    const p = pts[i];
    const q = pts[(i + 1) % pts.length];
    n = [
      n[0] + (p[1] - a[1]) * (q[2] - a[2]) - (p[2] - a[2]) * (q[1] - a[1]),
      n[1] + (p[2] - a[2]) * (q[0] - a[0]) - (p[0] - a[0]) * (q[2] - a[2]),
      n[2] + (p[0] - a[0]) * (q[1] - a[1]) - (p[1] - a[1]) * (q[0] - a[0]),
    ];
  }
  const lenN = Math.hypot(n[0], n[1], n[2]);
  if (lenN <= 1e-12 * maxSpan * maxSpan || !Number.isFinite(lenN)) return null;
  const nHat: Diem3 = [n[0] / lenN, n[1] / lenN, n[2] / lenN];
  const e1Raw: Diem3 = [
    nHat[1] * uRaw[2] - nHat[2] * uRaw[1],
    nHat[2] * uRaw[0] - nHat[0] * uRaw[2],
    nHat[0] * uRaw[1] - nHat[1] * uRaw[0],
  ];
  const lenE1 = Math.hypot(e1Raw[0], e1Raw[1], e1Raw[2]);
  if (lenE1 <= 1e-12 || !Number.isFinite(lenE1)) return null;
  const e1: Diem3 = [e1Raw[0] / lenE1, e1Raw[1] / lenE1, e1Raw[2] / lenE1];
  return [uRaw, e1];
}

/** Diện tích có dấu của đa giác 2D — shoelace. */
export function dienTichCoDau(xy: readonly (readonly [number, number])[]): number {
  let s = 0;
  for (let i = 0; i < xy.length; i += 1) {
    const p = xy[i];
    const q = xy[(i + 1) % xy.length];
    s += p[0] * q[1] - q[0] * p[1];
  }
  return s / 2;
}

function trongTamGiac(
  a: readonly [number, number], b: readonly [number, number],
  c: readonly [number, number], p: readonly [number, number],
): boolean {
  const d = (u: readonly [number, number], v: readonly [number, number],
             w: readonly [number, number]) =>
    (v[0] - u[0]) * (w[1] - u[1]) - (v[1] - u[1]) * (w[0] - u[0]);
  const d1 = d(a, b, p);
  const d2 = d(b, c, p);
  const d3 = d(c, a, p);
  const am = d1 < 0 || d2 < 0 || d3 < 0;
  const duong = d1 > 0 || d2 > 0 || d3 > 0;
  return !(am && duong);
}

/**
 * Đa giác phẳng đơn → danh sách tam giác, mỗi tam giác là ba CHỈ SỐ.
 *
 * Cắt tai (ear clipping) trên hệ toạ độ 2D cục bộ. Đa giác lồi cho đúng kết
 * quả như quạt cũ, nên nhánh lồi **không đổi hình**.
 *
 * Trả mảng rỗng khi đa giác suy biến (mọi đỉnh thẳng hàng, hoặc < 3 đỉnh) —
 * người gọi khi ấy không vẽ gì, thay vì vẽ một thứ vô nghĩa.
 */
export function chiaTamGiac(pts: readonly Diem3[]): [number, number, number][] {
  if (pts.length < 3) return [];
  if (pts.length === 3) {
    const [a, b, c] = pts;
    const u0 = b[0] - a[0], u1 = b[1] - a[1], u2 = b[2] - a[2];
    const v0 = c[0] - a[0], v1 = c[1] - a[1], v2 = c[2] - a[2];
    const lenU = Math.hypot(u0, u1, u2);
    const lenV = Math.hypot(v0, v1, v2);
    const area2 = Math.hypot(
      u1 * v2 - u2 * v1,
      u2 * v0 - u0 * v2,
      u0 * v1 - u1 * v0,
    );
    if (lenU <= 0 || lenV <= 0 || area2 <= 1e-10 * lenU * lenV) return [];
    return [[0, 1, 2]];
  }

  const truc = heTrucCucBo(pts);
  if (!truc) return [];
  const [e0, e1] = truc;
  const a = pts[0];
  const xy: [number, number][] = pts.map((p) => {
    const d: Diem3 = [p[0] - a[0], p[1] - a[1], p[2] - a[2]];
    return [
      d[0] * e0[0] + d[1] * e0[1] + d[2] * e0[2],
      d[0] * e1[0] + d[1] * e1[1] + d[2] * e1[2],
    ];
  });

  // Làm việc theo chiều DƯƠNG; đảo lại nếu biên đi theo chiều âm.
  let idx = pts.map((_, i) => i);
  if (dienTichCoDau(xy) < 0) idx = idx.slice().reverse();

  const ra: [number, number, number][] = [];
  let canh = 0;
  while (idx.length > 3 && canh < pts.length * pts.length + 8) {
    canh += 1;
    let catDuoc = false;
    for (let k = 0; k < idx.length; k += 1) {
      const i0 = idx[(k - 1 + idx.length) % idx.length];
      const i1 = idx[k];
      const i2 = idx[(k + 1) % idx.length];
      const [p0, p1, p2] = [xy[i0], xy[i1], xy[i2]];
      const l01 = Math.hypot(p1[0] - p0[0], p1[1] - p0[1]);
      const l02 = Math.hypot(p2[0] - p0[0], p2[1] - p0[1]);
      const cheo = (p1[0] - p0[0]) * (p2[1] - p0[1])
        - (p1[1] - p0[1]) * (p2[0] - p0[0]);
      if (cheo <= 1e-12 * l01 * l02) continue;     // đỉnh lõm hoặc thẳng hàng (bất biến tỷ lệ)
      const chua = idx.some((j) => j !== i0 && j !== i1 && j !== i2
        && trongTamGiac(p0, p1, p2, xy[j]));
      if (chua) continue;                          // có đỉnh khác nằm trong tai
      ra.push([i0, i1, i2]);
      idx.splice(k, 1);
      catDuoc = true;
      break;
    }
    // Không cắt được tai nào ⇒ đa giác không đơn (tự cắt). Dừng, đừng đoán.
    if (!catDuoc) return [];
  }
  if (idx.length === 3) ra.push([idx[0], idx[1], idx[2]]);
  return ra;
}
