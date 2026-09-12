/**
 * scene3d-nhan.ts — BỐ TRÍ NHÃN CÓ VẬT CẢN, ràng buộc CỨNG.
 *
 * ─── VÌ SAO TỒN TẠI ───────────────────────────────────────────────────────
 *
 * Bản trước đặt mọi nhãn ở đúng một chỗ (ngay trên điểm neo) rồi **ẩn** nhãn
 * nào chồng. Hai hậu quả đo được trên bài thật: nhãn `N` của thiết diện
 * `(MNP)` biến mất hẳn ở 1440×900, và `S` biến mất ở 390×844 — bài hỏi về
 * thiết diện MNP mà mất chữ N.
 *
 * Bản kế tiếp thử tám hướng × hai bán kính và cộng dồn ba khoản phạt. Nó vẫn
 * chưa đủ, vì nó **không biết gì về NÉT**: chữ đáp xuống đúng trên cạnh khối
 * và trên biên thiết diện — chỗ mắt cần đọc hình nhất, và chỗ nền không còn
 * trắng nên chữ mất tương phản.
 *
 * ─── HAI TẦNG, KHÔNG PHẢI MỘT HÀM PHẠT ────────────────────────────────────
 *
 * Gộp tất cả vào một tổng phạt thì một vị trí ĐÈ LÊN CẠNH vẫn thắng nếu nó
 * gần điểm neo hơn — một vi phạm mua được bằng điểm cộng ở tiêu chí khác.
 * Ở đây tách hẳn:
 *   · **ràng buộc cứng** — ứng viên vi phạm bị loại thẳng, không cách nào cứu;
 *   · **giá mềm** — chỉ để xếp hạng những ứng viên ĐÃ hợp lệ.
 *
 * Bốn nhóm vật cản: nét đã chiếu (đọc thẳng từ bộ đệm `instanceStart`/
 * `instanceEnd` của mọi `LineSegments2`, nên không bỏ sót vai nào và không cần
 * sổ đăng ký riêng) · điểm không phải neo của chính nhãn ấy · nhãn đã đặt ·
 * hộp DOM phủ lên canvas.
 *
 * ─── KHÔNG GIẤU CHỮ ───────────────────────────────────────────────────────
 *
 * Khi không còn ứng viên hợp lệ, hàm này **không** tự nới ngưỡng và **không**
 * giấu nhãn. Nó đặt nhãn ở chỗ ít vi phạm nhất và **khai tên nhãn ấy ra** để
 * nơi gọi lùi camera rồi thử lại (xem `LABEL_LAYOUT_UNSATISFIABLE` ở
 * `scene3d-view.tsx`). Nới ngầm là cách một bản dựng trông đạt mà không đạt.
 */
import * as THREE from "three";

export interface Doan {
  x1: number; y1: number; x2: number; y2: number;
}

export interface NhanVao {
  id: string;
  /** Điểm neo trên màn hình, pixel CSS. */
  x: number; y: number;
  /** Cỡ hộp chữ, pixel CSS. */
  rw: number; rh: number;
  uuTien: number;
}

export interface Hop { x: number; y: number; w: number; h: number }

export interface CanNhan {
  /** Khoảng cách tối thiểu nhãn ↔ nét, pixel CSS. 6 máy để bàn, 4 điện thoại. */
  kcCanh: number;
  /** Khoảng cách tối thiểu nhãn ↔ điểm không phải neo của nó. */
  kcDiem: number;
  /** Lề an toàn tới mép khung nhìn. */
  le: number;
  /** Bán kính thử cơ sở quanh điểm neo. */
  banKinh: number;
}

/** Mười sáu hướng thử, đều nhau. Tám hướng hay kẹt ở góc hẹp. */
const HUONG: [number, number][] = Array.from({ length: 16 }, (_, i) => {
  const a = (i * Math.PI) / 8;
  return [Math.cos(a), -Math.sin(a)] as [number, number];
});

/** Bốn bán kính. Gần trước, xa sau — xa là nhượng bộ, phải trả giá. */
const BOI_BAN_KINH = [1, 1.35, 1.75, 2.3];

/** Khoảng cách từ một điểm tới một đoạn thẳng. */
export function kcDiemDoan(px: number, py: number, d: Doan): number {
  const vx = d.x2 - d.x1, vy = d.y2 - d.y1;
  const L2 = vx * vx + vy * vy;
  if (L2 < 1e-12) return Math.hypot(px - d.x1, py - d.y1);
  let t = ((px - d.x1) * vx + (py - d.y1) * vy) / L2;
  t = Math.max(0, Math.min(1, t));
  return Math.hypot(px - (d.x1 + t * vx), py - (d.y1 + t * vy));
}

function catNhau(a: Doan, b: Doan): boolean {
  const d = (p: [number, number], q: [number, number], r: [number, number]) =>
    (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0]);
  const p1: [number, number] = [a.x1, a.y1], p2: [number, number] = [a.x2, a.y2];
  const p3: [number, number] = [b.x1, b.y1], p4: [number, number] = [b.x2, b.y2];
  const d1 = d(p3, p4, p1), d2 = d(p3, p4, p2), d3 = d(p1, p2, p3), d4 = d(p1, p2, p4);
  return ((d1 > 0) !== (d2 > 0)) && ((d3 > 0) !== (d4 > 0));
}

/**
 * Khoảng cách từ một hộp chữ tới một đoạn thẳng. `0` khi đoạn cắt hoặc nằm
 * trong hộp — nghĩa là chữ đang ĐÈ lên nét.
 */
export function kcHopDoan(h: Hop, d: Doan): number {
  const x1 = h.x, y1 = h.y, x2 = h.x + h.w, y2 = h.y + h.h;
  const trong = (x: number, y: number) => x >= x1 && x <= x2 && y >= y1 && y <= y2;
  if (trong(d.x1, d.y1) || trong(d.x2, d.y2)) return 0;
  const canh: Doan[] = [
    { x1, y1, x2, y2: y1 }, { x1: x2, y1, x2, y2 },
    { x1: x2, y1: y2, x2: x1, y2 }, { x1, y1: y2, x2: x1, y2: y1 },
  ];
  for (const c of canh) if (catNhau(c, d)) return 0;
  let m = Infinity;
  for (const [px, py] of [[x1, y1], [x2, y1], [x2, y2], [x1, y2]] as [number, number][]) {
    m = Math.min(m, kcDiemDoan(px, py, d));
  }
  for (const [px, py] of [[d.x1, d.y1], [d.x2, d.y2]] as [number, number][]) {
    const cx = Math.max(x1, Math.min(x2, px)), cy = Math.max(y1, Math.min(y2, py));
    m = Math.min(m, Math.hypot(px - cx, py - cy));
  }
  return m;
}

/** Hai hộp có chồng nhau không. */
function chongHop(a: Hop, b: Hop): boolean {
  return a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
}

/**
 * Mọi đoạn nét trong cây, đã chiếu ra màn hình.
 *
 * Đọc từ `instanceStart`/`instanceEnd` của `LineSegmentsGeometry` — đó là nơi
 * `Line2`/`LineSegments2` giữ toạ độ THẬT. ⚠️ `attributes.position` của chúng
 * là khuôn tám đỉnh của MỘT đoạn, tất cả nằm trên `z = 0`; đọc nhầm chỗ ấy sẽ
 * cho một chùm đoạn vô nghĩa quanh gốc toạ độ.
 *
 * Gom được cả cạnh khối, biên thiết diện, viền mặt phẳng, đường dựng và đường
 * thẳng vô hạn — chúng đi chung một lối dựng nên không vai nào lọt lưới, kể cả
 * vai mới thêm sau này.
 */
export function doanNetTrenMan(
  goc: THREE.Object3D, cam: THREE.Camera, w: number, h: number,
): Doan[] {
  const ra: Doan[] = [];
  const v = new THREE.Vector3();
  const chieu = (x: number, y: number, z: number, m: THREE.Matrix4) => {
    v.set(x, y, z).applyMatrix4(m).project(cam);
    return { x: ((v.x + 1) / 2) * w, y: ((1 - v.y) / 2) * h, z: v.z };
  };
  goc.traverse((vat) => {
    /* VÀNH THIẾT DIỆN — tròn và elip vẽ bằng `RingGeometry`, tức MESH, nên
     * chúng không có `instanceStart`. Nhánh dựng ghi lại mẫu vành vào
     * `userData.mauVanh`; không ghi thì bộ giải mù trước đúng cái biên mà bài
     * đang hỏi, và chữ đáp thẳng lên nó (đo được 1,5–5 px ở p3/p6/p7). */
    const mauVanh = vat.userData?.mauVanh as [number, number, number][] | undefined;
    if (mauVanh && mauVanh.length > 1) {
      vat.updateWorldMatrix(true, false);
      const M2 = vat.matrixWorld;
      for (let i = 0; i < mauVanh.length; i++) {
        const p = mauVanh[i], q = mauVanh[(i + 1) % mauVanh.length];
        const A2 = chieu(p[0], p[1], p[2], M2);
        const B2 = chieu(q[0], q[1], q[2], M2);
        if (A2.z > 1 || B2.z > 1) continue;
        ra.push({ x1: A2.x, y1: A2.y, x2: B2.x, y2: B2.y });
      }
    }
    if (!vat.userData?.net && !vat.userData?.baoDong) return;
    const g = (vat as THREE.Mesh).geometry as THREE.BufferGeometry | undefined;
    const s = g?.attributes?.instanceStart as THREE.BufferAttribute | undefined;
    const e = g?.attributes?.instanceEnd as THREE.BufferAttribute | undefined;
    if (!s || !e) return;
    vat.updateWorldMatrix(true, false);
    const M = vat.matrixWorld;
    for (let i = 0; i < s.count; i++) {
      const a = chieu(s.getX(i), s.getY(i), s.getZ(i), M);
      const b = chieu(e.getX(i), e.getY(i), e.getZ(i), M);
      if (a.z > 1 || b.z > 1) continue;                    // sau lưng camera
      ra.push({ x1: a.x, y1: a.y, x2: b.x, y2: b.y });
    }
  });
  return ra;
}

export interface ChoNhan { dx: number; dy: number; hop: Hop; kcNet: number; kcDiem: number }

export interface KetQuaNhan {
  /** Chỗ đã chốt cho từng nhãn. LUÔN có đủ mọi nhãn — không nhãn nào bị giấu. */
  cho: Map<string, ChoNhan>;
  /**
   * Nhãn KHÔNG tìm được chỗ thoả mọi ràng buộc cứng.
   *
   * Rỗng ⇒ bố trí đạt. Không rỗng ⇒ nơi gọi phải lùi camera rồi thử lại, và
   * nếu vẫn không được thì khai `LABEL_LAYOUT_UNSATISFIABLE`. Hàm này KHÔNG
   * tự nới ngưỡng: nới ngầm là cách một bản dựng trông đạt mà không đạt.
   */
  thieu: string[];
}

/**
 * Đặt nhãn. Nhãn ưu tiên cao đặt trước và **giữ chỗ**, nên một chữ quan trọng
 * không bị một chữ phụ đẩy ra rìa.
 */
export function giaiNhan(
  dat: NhanVao[], canh: Doan[], nut: Hop[], can: CanNhan, w: number, h: number,
): KetQuaNhan {
  const cho = new Map<string, ChoNhan>();
  const thieu: string[] = [];
  const daDat: Hop[] = [];
  const neo = dat.map((d) => ({ id: d.id, x: d.x, y: d.y }));

  /** Khoảng cách nhỏ nhất từ một hộp tới mọi nét. */
  const toiNet = (hop: Hop): number => {
    let m = Infinity;
    for (const c of canh) {
      const k = kcHopDoan(hop, c);
      if (k < m) m = k;
      if (m === 0) break;
    }
    return m;
  };
  /** Khoảng cách nhỏ nhất tới điểm neo của nhãn KHÁC. */
  const toiDiem = (hop: Hop, id: string): number => {
    let m = Infinity;
    for (const q of neo) {
      if (q.id === id) continue;
      const cx = Math.max(hop.x, Math.min(hop.x + hop.w, q.x));
      const cy = Math.max(hop.y, Math.min(hop.y + hop.h, q.y));
      m = Math.min(m, Math.hypot(q.x - cx, q.y - cy));
    }
    return m;
  };

  for (const d of [...dat].sort((a, b) => b.uuTien - a.uuTien || a.id.localeCompare(b.id))) {
    let tot: { c: ChoNhan; gia: number } | null = null;
    let doVay: { c: ChoNhan; pham: number } | null = null;

    for (let bi = 0; bi < BOI_BAN_KINH.length; bi++) {
      const R = can.banKinh * BOI_BAN_KINH[bi];
      for (const [ux, uy] of HUONG) {
        const dx = ux * R, dy = uy * R;
        const hop: Hop = { x: d.x + dx - d.rw / 2, y: d.y + dy - d.rh / 2, w: d.rw, h: d.rh };

        // ── RÀNG BUỘC CỨNG ────────────────────────────────────────────────
        const raKhung = Math.max(
          can.le - hop.x, can.le - hop.y,
          hop.x + hop.w - (w - can.le), hop.y + hop.h - (h - can.le), 0,
        );
        const deNhan = daDat.some((o) => chongHop(hop, o));
        const deNut = nut.some((n) => chongHop(hop, n));
        const kcNet = toiNet(hop);
        const kcDiem = toiDiem(hop, d.id);
        const hopLe = raKhung === 0 && !deNhan && !deNut
          && kcNet >= can.kcCanh && kcDiem >= can.kcDiem;

        const c: ChoNhan = { dx, dy, hop, kcNet, kcDiem };
        if (hopLe) {
          // ── GIÁ MỀM: chỉ xếp hạng ứng viên ĐÃ hợp lệ ────────────────────
          let gia = bi * 10;                       // gần điểm neo hơn thì tốt hơn
          gia += Math.max(0, 18 - kcNet) * 0.6;    // càng thoáng nét càng tốt
          gia += uy > 0 ? 2 : 0;                   // nhẹ nhàng ưu tiên phía trên
          if (!tot || gia < tot.gia) tot = { c, gia };
        } else {
          /* Chỗ ĐỠ NHẤT khi mọi ứng viên đều vi phạm. Đè lên nhãn khác hoặc
             lọt dưới nút điều khiển là hai thứ tệ nhất — chữ khi ấy không đọc
             được chút nào — nên phạt nặng hơn hẳn thiếu khoảng cách. */
          const pham = raKhung * 20 + (deNhan ? 800 : 0) + (deNut ? 800 : 0)
            + Math.max(0, can.kcCanh - kcNet) * 12
            + Math.max(0, can.kcDiem - kcDiem) * 4 + bi;
          if (!doVay || pham < doVay.pham) doVay = { c, pham };
        }
      }
    }

    const chot = tot?.c ?? doVay?.c;
    if (!chot) continue;                            // không có cả chỗ đỡ nhất
    cho.set(d.id, chot);
    daDat.push(chot.hop);
    if (!tot) thieu.push(d.id);
  }
  return { cho, thieu };
}
