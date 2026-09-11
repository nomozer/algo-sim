/**
 * scene3d-wide-line.ts — NÉT CÓ BỀ DÀY THẬT, tính bằng pixel CSS.
 *
 * ─── VÌ SAO TỒN TẠI ───────────────────────────────────────────────────────
 *
 * `THREE.LineBasicMaterial.linewidth` **bị WebGL bỏ qua**: mọi `THREE.Line`
 * đều vẽ ra đúng 1 px, bất kể khai bao nhiêu. Nên bảng token nói *"cạnh thấy
 * 2,8 px · cạnh khuất 1,6 px · thiết diện 3,5 px"* mà renderer lại vẽ 1 px cho
 * tất cả — cả ba vai đọc ra ngang hàng, và hình mất đúng thứ phân biệt
 * *"cạnh này ở trước hay ở sau"*. Ảnh sản phẩm thật đo được: trung vị bề dày
 * ~1 px trên cả bảy ca, trong khi mockup đã duyệt có ba bậc rõ rệt.
 *
 * `Line2`/`LineSegments2` dựng mỗi đoạn thành một dải tam giác trong không
 * gian màn hình, nên bề dày là bề dày THẬT và không phình theo khoảng cách
 * camera.
 *
 * ─── ĐỘ PHÂN GIẢI: VÌ SAO LẤY KÍCH THƯỚC CSS, KHÔNG LẤY BUFFER ───────────
 *
 * Shader của `LineMaterial` tính `offset_ndc = linewidth / resolution.y`. Đổi
 * sang pixel màn hình thì bề dày `= linewidth × drawingBufferHeight /
 * resolution.y`. Cho `resolution.y` = chiều cao **CSS** thì
 * `drawingBufferHeight = cssH × DPR` và bề dày tính theo pixel CSS đúng bằng
 * `linewidth` — **ở mọi `devicePixelRatio`**. Đó là lý do ở đây luôn truyền
 * kích thước CSS; truyền kích thước buffer sẽ cho nét mảnh đi DPR lần trên
 * màn hình retina.
 *
 * ⚠️ `LineMaterial.resolution` có setter **`.copy(value)`**, không giữ tham
 * chiếu. Nên không chia sẻ được một `Vector2` chung: mỗi vật liệu phải được
 * gán lại khi khung đổi cỡ. `capNhatDoPhanGiai` quét cây và làm việc ấy.
 */
import * as THREE from "three";
import { Line2 } from "three/examples/jsm/lines/Line2.js";
import { LineSegments2 } from "three/examples/jsm/lines/LineSegments2.js";
import { LineGeometry } from "three/examples/jsm/lines/LineGeometry.js";
import { LineSegmentsGeometry } from "three/examples/jsm/lines/LineSegmentsGeometry.js";
import { LineMaterial } from "three/examples/jsm/lines/LineMaterial.js";

/**
 * Bề dày theo VAI, đơn vị pixel CSS. Token đã duyệt ở vòng mockup tĩnh.
 *
 * Đây là một THANG BẬC chứ không phải sáu số rời: cạnh thấy phải đọc được là
 * đậm hơn cạnh khuất, và thiết diện phải đậm hơn cả hai vì nó là tiêu điểm
 * của bài. Đổi một số mà không nhìn hai số kề là làm phẳng thang bậc.
 */
export const BE_DAY_PX = {
  /** Cạnh khối, phần THẤY. */
  canhThay: 2.8,
  /** Cạnh khối, phần KHUẤT — mảnh hơn và đứt nét. */
  canhKhuat: 1.6,
  /** Biên thiết diện, phần THẤY. Đậm nhất trong cảnh. */
  thietDienThay: 3.5,
  /** Biên thiết diện, phần KHUẤT. */
  thietDienKhuat: 2.2,
  /** Đường dựng, trục khối. */
  duongDung: 1.2,
  /** Viền miếng mặt phẳng. */
  vienMatPhang: 1.2,
} as const;

/** Tỉ lệ khoảng trống trên nét của đường đứt — token "7/5". */
export const DASH_TREN_GAP = 7 / 5;

/**
 * Kích thước khung vẽ hiện tại, đơn vị CSS. Vật liệu mới dựng lấy giá trị này
 * ngay lúc tạo, nên một cảnh dựng lại giữa hai lần resize vẫn đúng bề dày.
 *
 * Giá trị mặc định chỉ dùng cho test và cho khoảnh khắc trước khi khung đo
 * được lần đầu; nó không bao giờ tới màn hình thật.
 */
const KHUNG = { rong: 1280, cao: 720 };

export function datKichThuocKhung(rong: number, cao: number): void {
  if (Number.isFinite(rong) && rong > 0) KHUNG.rong = rong;
  if (Number.isFinite(cao) && cao > 0) KHUNG.cao = cao;
}

export function kichThuocKhung(): { rong: number; cao: number } {
  return { ...KHUNG };
}

/** Vật liệu nét có phải `LineMaterial` không — dùng cho phép quét cây. */
export function laVatLieuNet(m: unknown): m is LineMaterial {
  return !!m && (m as { isLineMaterial?: boolean }).isLineMaterial === true;
}

/**
 * Gán lại `resolution` cho mọi vật liệu nét trong một cây.
 *
 * Gọi khi khung đổi cỡ. Quét cây thay vì giữ một sổ đăng ký: sổ đăng ký phải
 * được gỡ tay lúc huỷ vật liệu, và quên gỡ là rò bộ nhớ im lặng. Cảnh ở đây
 * chỉ vài chục vật nên quét là rẻ, và nó chỉ chạy lúc resize.
 */
export function capNhatDoPhanGiai(goc: THREE.Object3D, rong: number, cao: number): number {
  datKichThuocKhung(rong, cao);
  let n = 0;
  goc.traverse((vat) => {
    const m = (vat as THREE.Mesh).material;
    for (const x of Array.isArray(m) ? m : [m]) {
      if (laVatLieuNet(x)) { x.resolution.set(KHUNG.rong, KHUNG.cao); n += 1; }
    }
  });
  return n;
}

export interface TuyChonNet {
  mau: number;
  /** Bề dày, pixel CSS. */
  beDayPx: number;
  /** Nét đứt. `chuKy` tính bằng ĐƠN VỊ THẾ GIỚI, theo tỉ lệ cảnh. */
  dut?: boolean;
  chuKy?: number;
  depthFunc?: THREE.DepthModes;
  depthWrite?: boolean;
  opacity?: number;
}

/**
 * Vật liệu nét. `worldUnits = false` ⇒ bề dày theo màn hình, không phình theo
 * khoảng cách camera — đúng như bảng token mô tả.
 */
export function taoVatLieuNet(t: TuyChonNet): LineMaterial {
  const m = new LineMaterial({
    color: t.mau,
    linewidth: t.beDayPx,
    worldUnits: false,
    dashed: !!t.dut,
    alphaToCoverage: true,
    /* Đẩy nhẹ về phía camera: đường NẰM TRÊN mặt khối (vành đáy, biên thiết
     * diện) sẽ nhấp nháy nếu chiều sâu của nó bằng đúng chiều sâu của mặt. */
    polygonOffset: true,
    polygonOffsetFactor: -2,
    polygonOffsetUnits: -2,
  });
  m.resolution.set(KHUNG.rong, KHUNG.cao);
  if (t.dut) {
    const chuKy = t.chuKy && t.chuKy > 0 ? t.chuKy : 1;
    m.dashSize = chuKy;
    m.gapSize = chuKy / DASH_TREN_GAP;
  }
  if (t.depthFunc !== undefined) m.depthFunc = t.depthFunc;
  if (t.depthWrite !== undefined) m.depthWrite = t.depthWrite;
  if (t.opacity !== undefined && t.opacity < 1) {
    m.transparent = true;
    m.opacity = t.opacity;
  }
  return m;
}

/** Mảng toạ độ phẳng của một `BufferGeometry` có thuộc tính `position`. */
function toaDoPhang(g: THREE.BufferGeometry): number[] {
  const p = g.getAttribute("position");
  if (!p) return [];
  const ra: number[] = [];
  for (let i = 0; i < p.count; i++) ra.push(p.getX(i), p.getY(i), p.getZ(i));
  return ra;
}

/**
 * Dựng một vật nét có bề dày từ `BufferGeometry` thường.
 *
 * `lienMach = true` ⇒ đường gấp khúc nối tiếp (`Line2`); `false` ⇒ từng đoạn
 * rời, dạng `EdgesGeometry` sinh ra (`LineSegments2`).
 *
 * ⚠️ `computeLineDistances()` là BẮT BUỘC khi nét đứt — thiếu nó thì đường
 * đứt vẽ ra liền, và phần khuất đọc y hệt phần thấy.
 */
export function taoNet(
  g: THREE.BufferGeometry, lienMach: boolean, vatLieu: LineMaterial,
): Line2 | LineSegments2 {
  const toaDo = toaDoPhang(g);
  let d: Line2 | LineSegments2;
  if (lienMach) {
    const hh = new LineGeometry();
    hh.setPositions(toaDo);
    d = new Line2(hh, vatLieu);
  } else {
    const hh = new LineSegmentsGeometry();
    hh.setPositions(toaDo);
    d = new LineSegments2(hh, vatLieu);
  }
  d.computeLineDistances();
  /* ⚠️ `Line2` và `LineSegments2` KẾ THỪA `THREE.Mesh`, nên `isMesh === true`
   * và `geometry.attributes.position` tồn tại — nhưng position ấy là **khuôn
   * của một đoạn** (tám đỉnh, tất cả nằm trên z = 0), không phải hình thật.
   * Bất kỳ phép quét nào đếm tam giác hay đọc toạ độ theo `isMesh` sẽ nhặt
   * phải khuôn đó: phép đo diện tích chiếu của đáy khối lõm đọc ra 14 thay vì
   * 10 đúng vì lý do này. Cờ dưới đây để những phép quét ấy loại được vật nét
   * ra, cùng lối với `userData.chieuSau`. */
  d.userData.net = true;
  return d;
}
