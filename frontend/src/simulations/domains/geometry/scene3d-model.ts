/**
 * Scene3D — kiểu dữ liệu + phép chiếu THUẦN cho renderer hình học không gian.
 *
 *   Semantic Program → Interpreter → SimulationState → Scene3D → **đây** → three.js
 *
 * File này KHÔNG import `three`. Đó là chủ đích: mọi thứ quyết định *cái gì hiện
 * ra ở bước nào* đều kiểm được mà không cần WebGL, và tầng vẽ chỉ còn lại việc
 * đặt mesh. Cùng khuôn `encap-ui3d.tsx` đã chứng minh (`layerDepth`/`sideX` là
 * hàm thuần, tách khỏi `Encap3DWorkspace`).
 *
 * ─── HAI RANH GIỚI, VÀ CHÚNG LÀ LÝ DO FILE NÀY TỒN TẠI ────────────────────
 *
 * ① KHÔNG TÍNH HÌNH HỌC. Không tích có hướng, không giao điểm, không suy quan
 *    hệ. Mọi toạ độ/pháp tuyến/vector chỉ phương đến từ kernel hữu tỉ ở backend.
 *    Renderer chỉ ĐẶT và ĐỊNH HƯỚNG những thứ đã được tính.
 *
 * ② `toNumber` là chỗ DUY NHẤT số hoá float trong toàn chuỗi. Backend giữ chuỗi
 *    phân số (`"1/2"`) tới tận đây vì kernel so **bằng đúng**, không epsilon —
 *    hoá float sớm là vứt bỏ đúng thứ phân biệt hệ này với một bộ vẽ hình.
 *    GPU cần float, nên phép ấy phải xảy ra; nó chỉ không được xảy ra sớm hơn.
 */

/** Toạ độ chính xác: chuỗi phân số như `"0"`, `"2"`, `"1/2"`, `"-3/4"`. */
export type Exact = string;
export type ExactVec3 = [Exact, Exact, Exact];
export type Vec3 = [number, number, number];

/**
 * Loại hình vẽ — **ĐỒNG BỘ CỨNG** với `scene3d.RENDER_HINT` ở backend.
 *
 * Khoá bằng `tests/geometry/test_scene3d_ts_sync.py`: thêm một loại ở Python mà
 * quên nhánh ở đây thì renderer sẽ **im lặng bỏ qua** đối tượng — đúng chế độ
 * hỏng của bất biến #33 (đã xảy ra thật với `bar_chart`).
 */
export const RENDER_KINDS = [
  "point_marker",
  "line",
  "surface",
  "mesh",
  "polygon",
  "readout",
] as const;
export type RenderKind = (typeof RENDER_KINDS)[number];

export interface SceneObject {
  id: string;
  label: string;
  type: string;
  render: RenderKind;
  origin: "free" | "derived";
  producer: string | null;
  depends: string[];
  xyz?: ExactVec3;
  point?: ExactVec3;
  direction?: ExactVec3;
  normal?: ExactVec3;
  vertices?: ExactVec3[];
  faces?: number[][];
  polygon?: ExactVec3[];
  closed?: boolean;
  value?: Exact;
}

export type EventAction = "INIT" | "CREATE" | "EXTEND" | "MEASURE" | "STEP";

export interface SceneEvent {
  step_index: number;
  action: EventAction;
  object: string | null;
  depends: string[];
  explanation: string;
}

export interface Scene3D {
  objects: SceneObject[];
  events: SceneEvent[];
  free_objects: string[];
}

/**
 * Chuỗi phân số → `number`. **Chỗ duy nhất** float xuất hiện.
 *
 * `"1/2"` → `0.5`, `"-3/4"` → `-0.75`, `"2"` → `2`. Không dùng `eval` cũng
 * không `Number("1/2")` (trả `NaN`) — tách tử/mẫu tường minh.
 *
 * Chuỗi hỏng ném lỗi thay vì trả `NaN`: một `NaN` lọt vào buffer của three.js
 * làm cả mesh biến mất **không báo gì**, và truy ngược từ một khung hình trống
 * về một chuỗi sai là chỗ tốn nhiều giờ nhất.
 */
export function toNumber(s: Exact): number {
  const t = String(s).trim();
  const m = /^(-?\d+)(?:\/(\d+))?$/.exec(t);
  if (!m) throw new Error(`Toạ độ không phải phân số hợp lệ: ${JSON.stringify(s)}`);
  const tu = Number(m[1]);
  const mau = m[2] === undefined ? 1 : Number(m[2]);
  if (mau === 0) throw new Error(`Mẫu số bằng 0: ${JSON.stringify(s)}`);
  return tu / mau;
}

export function toVec3(v: ExactVec3): Vec3 {
  return [toNumber(v[0]), toNumber(v[1]), toNumber(v[2])];
}

/** Số bước của mô phỏng. `0` khi cảnh chưa có sự kiện nào. */
export function stepCount(scene: Scene3D): number {
  return scene.events.length;
}

export function clampStep(scene: Scene3D, step: number): number {
  const n = stepCount(scene);
  if (n === 0) return 0;
  return Math.min(Math.max(Math.trunc(step), 0), n - 1);
}

/**
 * Những đối tượng ĐÃ TỒN TẠI tại bước `step`.
 *
 * ─── VÌ SAO TÍNH TỪ `events`, KHÔNG TỪ `objects` ────────────────────────
 *
 * `objects` là trạng thái CUỐI — mọi thứ đã dựng xong. Chiếu thẳng nó ra màn
 * hình thì học sinh thấy ngay hình hoàn chỉnh, và toàn bộ mục tiêu sư phạm
 * (*"một hình được hình thành như thế nào"*) biến mất.
 *
 * `events` mang thứ tự dựng thật, một sự kiện cho đúng một bước (bất biến #31).
 * Nên tập hiện ra ở bước `k` = mọi đối tượng có sự kiện tạo nó ở bước ≤ `k`,
 * cộng các đối tượng TỰ DO (điểm gốc của hệ trục) vốn có mặt từ bước `INIT`.
 */
export function objectsAt(scene: Scene3D, step: number): SceneObject[] {
  const k = clampStep(scene, step);
  const hien = new Set(scene.free_objects);
  for (const e of scene.events) {
    if (e.step_index > k) break;
    if (e.object) hien.add(e.object);
  }
  return scene.objects.filter((o) => hien.has(o.id));
}

/** Đối tượng vừa được tạo/kéo dài ở bước này — dùng để làm nổi bật. */
export function highlightedAt(scene: Scene3D, step: number): string[] {
  const k = clampStep(scene, step);
  const e = scene.events.find((x) => x.step_index === k);
  if (!e || !e.object) return [];
  return [e.object, ...e.depends];
}

/** Lời kể của bước hiện tại — Tier 1, do engine sinh từ trạng thái thật. */
export function narrationAt(scene: Scene3D, step: number): string {
  const e = scene.events.find((x) => x.step_index === clampStep(scene, step));
  return e ? e.explanation : "";
}

/**
 * Kích thước hiển thị của mặt phẳng và độ dài nửa đoạn của đường thẳng.
 *
 * `plane3` và `line3` là **VÔ HẠN** — backend cố ý không gửi biên, vì cắt chúng
 * là quyết định TRÌNH BÀY. Hai hằng dưới đây là quyết định ấy, và chúng thuộc
 * renderer: đổi chúng không đổi một mệnh đề toán học nào.
 */
export const PLANE_DISPLAY_SIZE = 6;
export const LINE_DISPLAY_HALF_LENGTH = 6;

/* ══ PHÁT LẠI — hàm THUẦN, không React, không three ══════════════════════
 *
 * Người học điều khiển **thời gian quan sát** và **góc nhìn**. Không điều khiển
 * nội dung toán học. Nên toàn bộ "tương tác" của Phase 5E rút gọn thành: đổi
 * MỘT SỐ NGUYÊN `step`.
 *
 * Đó là lý do nhóm hàm này thuần và nhỏ: nếu playback cần biết gì về hình học
 * thì thiết kế đã sai chỗ nào đó.
 */

export function isFirstStep(scene: Scene3D, step: number): boolean {
  return clampStep(scene, step) <= 0;
}

export function isLastStep(scene: Scene3D, step: number): boolean {
  const n = stepCount(scene);
  return n === 0 || clampStep(scene, step) >= n - 1;
}

export function nextStep(scene: Scene3D, step: number): number {
  return clampStep(scene, clampStep(scene, step) + 1);
}

export function prevStep(scene: Scene3D, step: number): number {
  return clampStep(scene, clampStep(scene, step) - 1);
}

/** Đối tượng đang được dựng ở bước này, và những thứ nó phụ thuộc. */
export function focusAt(
  scene: Scene3D,
  step: number,
): { created: string | null; depends: string[] } {
  const e = scene.events.find((x) => x.step_index === clampStep(scene, step));
  return { created: e?.object ?? null, depends: e ? [...e.depends] : [] };
}

/**
 * Người dùng đã bật "giảm chuyển động" ở hệ điều hành chưa?
 *
 * ─── VÌ SAO CẦN Ở TẦNG JS, DÙ W13-A11Y ĐÃ LÀM Ở CSS ────────────────────
 *
 * Khối `@media (prefers-reduced-motion: reduce)` trong `global.css` tắt được
 * `animation`/`transition` — tức hoạt cảnh do **CSS** phát. Tự động chạy các
 * bước dựng là hoạt cảnh do **JavaScript** phát: nó đổi nội dung khung hình
 * theo nhịp, và không luật CSS nào chạm tới được.
 *
 * Bỏ qua chỗ này thì người bật giảm-chuyển-động vẫn nhận đúng thứ họ đã tắt,
 * chỉ khác đường đi.
 *
 * SSR-an toàn: không có `window`/`matchMedia` ⇒ trả `false` (không tự suy diễn
 * sở thích của một người chưa có mặt).
 */
export function prefersReducedMotion(): boolean {
  if (typeof window === "undefined" || !window.matchMedia) return false;
  try {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  } catch {
    return false;
  }
}

/** Nhịp phát mặc định (ms/bước). Đủ chậm để đọc được lời kể của bước. */
export const PLAYBACK_INTERVAL_MS = 1400;
