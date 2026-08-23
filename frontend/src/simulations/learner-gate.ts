/**
 * LEARNER-FACING GATE — hợp đồng dùng chung cho MỌI mô phỏng sinh ra.
 *
 * ─── VÌ SAO TỒN TẠI ────────────────────────────────────────────────────────
 *
 * Sự cố vNext đã chụp được màn hình: lời kể chạy tới bước 6 ("đẩy `[` vào ngăn
 * xếp") trong khi hình ngăn xếp vẫn RỖNG. Cả hai tầng đều "xanh" theo tiêu chí
 * của chính nó — engine chạy đúng, renderer vẽ đúng cái nó được đưa — nhưng
 * người học nhìn thấy một điều SAI. Không cổng nào hỏi câu bắc qua hai tầng:
 *
 *     thứ hiện trên màn hình CÓ PHẢI trạng thái của khung đang xem không?
 *
 * Module này hỏi đúng câu đó, và hỏi cho mọi primitive chứ không riêng ngăn
 * xếp — `servable=true` là một tuyên bố về **người học**, nên nó phải được
 * chứng minh trên bề mặt người học nhìn thấy.
 *
 * ─── PHÉP CHIẾU ĐỌC CHỮ NHÌN THẤY, KHÔNG ĐỌC THUỘC TÍNH ───────────────────
 *
 * `projectSemanticDom` chỉ lấy nội dung `<text>` — đúng thứ hiện trên màn hình.
 * `data-obj` chỉ dùng để biết chữ nào THUỘC VỀ đối tượng nào, không bao giờ
 * dùng làm giá trị. Nếu lấy giá trị từ `data-*` thì renderer có thể khai một
 * đằng vẽ một nẻo mà guard vẫn xanh — tức là guard tự bịt mắt mình.
 */
import { displayLabel } from "./domains/generic/model";
import type { SimulationSpec } from "./domains/generic/model";

/** Chuỗi kỹ thuật KHÔNG BAO GIỜ được lọt lên bề mặt học sinh (§G). */
export const PLACEHOLDER_LEAKS = [
  "undefined",
  "null",
  "[object Object]",
  "NaN",
  "Infinity",
] as const;

/**
 * Primitive mà giá trị là MỘT DÃY PHẦN TỬ, không phải một ô chữ.
 *
 * Danh sách này quyết định cách đọc một collection RỖNG: với chúng, vắng
 * `data-item` = rỗng thật. Với primitive vô hướng thì ngược lại — giá trị nằm
 * ngay trong `<text>` và phải đọc bằng nhánh dự phòng.
 */
const LA_COLLECTION = new Set(["stack_view", "queue_view", "array_strip"]);

function kieuCua(spec: SimulationSpec, id: string): string {
  return spec.objects.find((o) => o.id === id)?.type ?? "";
}

export interface ObjectProjection {
  id: string;
  role: string;
  /** Chữ người học NHÌN THẤY, đã bỏ nhãn — theo thứ tự xuất hiện trong DOM. */
  values: string[];
  /** Nhãn hiển thị, giữ riêng để phân biệt "nhãn" với "giá trị". */
  label: string;
}

/** Gỡ thực thể HTML mà `renderToString` sinh ra, để so được với chuỗi gốc. */
function unescape(s: string): string {
  return s
    .replace(/&quot;/g, '"')
    .replace(/&#x27;/g, "'")
    .replace(/&#39;/g, "'")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">");
}

/**
 * Cắt ra đoạn HTML của một `<g>` kể từ `from`, khớp thẻ CÂN BẰNG.
 *
 * Không dùng regex tham lam/lười: đối tượng nào cũng chứa `<g>` lồng bên trong
 * (từng phần tử ngăn xếp là một `<g>`), nên `.*?</g>` cắt cụt ở phần tử đầu
 * tiên còn `.*</g>` nuốt sang đối tượng kế. Cả hai đều sai một cách IM LẶNG —
 * guard vẫn chạy, chỉ là chấm nhầm dữ liệu.
 */
function balancedG(html: string, from: number): string {
  let depth = 0;
  let i = from;
  while (i < html.length) {
    const open = html.indexOf("<g", i);
    const close = html.indexOf("</g>", i);
    if (close === -1) return html.slice(from);
    if (open !== -1 && open < close) {
      depth++;
      i = open + 2;
    } else {
      depth--;
      if (depth === 0) return html.slice(from, close + 4);
      i = close + 4;
    }
  }
  return html.slice(from);
}

/**
 * TRẠNG THÁI NGỮ NGHĨA ĐỌC TỪ MÀN HÌNH — khoá theo `id` đối tượng của spec.
 *
 * Đây là vế trái của bất biến §C. Vế phải là `valuesOf(spec, frame.values)`.
 * Hai vế lệch nhau theo bất kỳ chiều nào đều là FAIL, và chiều nào lệch nói
 * đúng lỗi gì: DOM đổi mà engine đứng yên ⇒ renderer tự tính; engine đổi mà DOM
 * đứng yên ⇒ renderer bỏ qua kênh giá trị.
 */
export function projectSemanticDom(
  html: string,
  spec: SimulationSpec,
): Record<string, ObjectProjection> {
  const ra: Record<string, ObjectProjection> = {};
  const rx = /<g[^>]*data-obj="([^"]*)"[^>]*data-role="([^"]*)"[^>]*>/g;
  let m: RegExpExecArray | null;
  while ((m = rx.exec(html)) !== null) {
    const id = unescape(m[1]);
    const doan = balancedG(html, m.index);
    const label = displayLabel(spec, id);

    /* HAI LOẠI CHỮ, và lẫn chúng là hỏng phép chiếu.
     *
     * Collection nào cũng vẽ kèm CHÚ GIẢI: `← TOP` ở đỉnh ngăn xếp,
     * `FRONT`/`REAR` hai đầu hàng đợi, `[0] [1] [2]` dưới dải mảng. Đó là
     * affordance ĐÚNG — §H còn đòi phải có. Nhưng chúng không phải dữ liệu, nên
     * bản đầu của guard này chấm `["{", "← TOP"]` là nội dung ngăn xếp rồi đỏ
     * oan ở cả ba miền.
     *
     * Nên: có `data-item` thì CHỈ đọc chúng (renderer đã nói rõ chữ nào là phần
     * tử); không có thì rơi về "mọi chữ trừ nhãn" — đúng cho `value_box`,
     * `node`, và mọi primitive vô hướng.
     *
     * `data-item` phân LOẠI chứ không cấp GIÁ TRỊ: giá trị vẫn là nội dung
     * `<text>` mà người học nhìn thấy. */
    const items = [...doan.matchAll(/<text[^>]*\sdata-item="[^"]*"[^>]*>([^<]*)<\/text>/g)]
      .map((t) => unescape(t[1]));

    let vals: string[];
    if (items.length > 0 || LA_COLLECTION.has(kieuCua(spec, id))) {
      /* Collection RỖNG cũng đi nhánh này, và đó là điểm mấu chốt: không có
       * `data-item` nào nghĩa là **không có phần tử**, chứ không phải "hãy đọc
       * chú giải". Bản trước rơi về nhánh dự phòng và chấm `["FRONT","REAR"]`
       * làm nội dung hàng đợi rỗng — sai đúng ở khung khởi tạo, khung mà mọi mô
       * phỏng đều đi qua. */
      vals = items;
    } else {
      vals = [...doan.matchAll(/<text[^>]*>([^<]*)<\/text>/g)].map((t) => unescape(t[1]));
      // Bỏ ĐÚNG MỘT lần xuất hiện của nhãn. Bỏ mọi lần sẽ nuốt luôn giá trị
      // trùng chữ với nhãn — hiếm, nhưng khi xảy ra thì guard sai mà không ai biết.
      const iNhan = vals.indexOf(label);
      if (iNhan >= 0) vals.splice(iNhan, 1);
    }
    ra[id] = { id, role: unescape(m[2]), values: vals, label };
  }
  return ra;
}

/** Mọi chuỗi kỹ thuật rò lên bề mặt học sinh, kèm chỗ rò (§G). */
export function findPlaceholderLeaks(
  html: string,
  spec: SimulationSpec,
): string[] {
  const chieu = projectSemanticDom(html, spec);
  const ra: string[] = [];
  for (const p of Object.values(chieu)) {
    for (const v of p.values) {
      for (const xau of PLACEHOLDER_LEAKS) {
        // So BẰNG NHAU, không phải `includes`: một giá trị dữ liệu thật có thể
        // chứa chữ "null" như một phần nội dung, và bắt nó là kêu oan.
        if (v.trim() === xau) ra.push(`${p.id}: "${v}"`);
      }
    }
  }
  return ra;
}

/**
 * `0` THẬT khác `chưa có` — kiểm cả hai chiều (§G).
 *
 * Bẫy đã cắn kho này một lần (`o.value ?? 0`): ô chưa có dữ liệu in ra `0` như
 * thật. Bản vá cho lỗi đó lại có thể đẻ ra lỗi ngược — nuốt luôn số 0 hợp lệ.
 * Nên guard phải phát biểu cả hai vế, không chỉ vế vừa cháy.
 */
export function zeroKhongBiNuot(
  chieu: Record<string, ObjectProjection>,
  id: string,
): boolean {
  return (chieu[id]?.values ?? []).includes("0");
}

export interface TimelineModuleLike<S> {
  init(spec: SimulationSpec): S;
  timeline?: {
    stepCount(s: S): number;
    currentStep(s: S): number;
    goToStep(s: S, step: number): S;
  };
}

export interface TransportReport {
  ok: boolean;
  loi: string[];
  stepCount: number;
}

/**
 * §A — TRANSPORT ĐI QUA ĐÚNG HỢP ĐỒNG ENGINE, và trạng thái lịch sử khôi phục
 * được.
 *
 * `chieuTrangThai` là hàm rút trạng thái ngữ nghĩa của một state (thường là
 * `valuesOf(spec, frame.values)`), do phía gọi cung cấp — gate không được biết
 * primitive nào, nếu không nó lại thành gate riêng cho một miền.
 *
 * BẤT BIẾN QUAN TRỌNG NHẤT Ở ĐÂY: `prev` phải khôi phục ĐÚNG trạng thái lịch
 * sử, không phải "một trạng thái trông giống". Nên phép kiểm là đi tới cuối
 * timeline rồi lùi từng bước, so với bảng đã chụp lúc đi xuôi. Một engine tính
 * tiến-lùi bằng cách hoàn tác gần đúng sẽ trượt ngay tại đây.
 */
export function kiemTransport<S>(
  mod: TimelineModuleLike<S>,
  spec: SimulationSpec,
  chieuTrangThai: (s: S) => unknown,
): TransportReport {
  const loi: string[] = [];
  const tl = mod.timeline;
  if (!tl) return { ok: true, loi: ["N/A — module không khai timeline"], stepCount: 0 };

  const s0 = mod.init(spec);
  const n = tl.stepCount(s0);
  const ky = (s: S) => JSON.stringify(chieuTrangThai(s));

  // Đi xuôi, chụp lại từng khung.
  const xuoi: string[] = [];
  let s = s0;
  for (let k = 0; k < n; k++) {
    s = tl.goToStep(s, k);
    if (tl.currentStep(s) !== k) loi.push(`NEXT: xin khung ${k}, con trỏ ở ${tl.currentStep(s)}`);
    xuoi.push(ky(s));
  }

  // Đi ngược, so với bảng đã chụp.
  for (let k = n - 1; k >= 0; k--) {
    s = tl.goToStep(s, k);
    if (ky(s) !== xuoi[k]) loi.push(`PREVIOUS: khung ${k} khôi phục SAI trạng thái lịch sử`);
  }

  // RESET = về đúng khung khởi tạo, không phải "gần giống".
  const veDau = tl.goToStep(s, 0);
  if (ky(veDau) !== xuoi[0]) loi.push("RESET: không trở về trạng thái khởi tạo");
  if (tl.currentStep(veDau) !== 0) loi.push("RESET: con trỏ không về 0");

  // SCRUB nhảy cóc phải dựng đúng khung đích, không suy từ khung hiện tại.
  for (const k of [n - 1, 0, Math.floor(n / 2), n - 1]) {
    if (k < 0 || k >= n) continue;
    if (ky(tl.goToStep(s0, k)) !== xuoi[k]) loi.push(`SCRUB: nhảy thẳng tới ${k} ra state khác khi đi tuần tự`);
  }

  // PLAY không được bỏ khung: đi hết timeline phải chạm ĐỦ n trạng thái.
  if (new Set(xuoi).size < 2 && n > 1) {
    loi.push("PLAY: timeline có nhiều khung nhưng trạng thái ngữ nghĩa không đổi");
  }

  return { ok: loi.length === 0, loi, stepCount: n };
}

/** Kẹp chỉ số phải là KẸP, không phải quay vòng (§A — biên của transport). */
export function kiemBienTimeline<S>(
  mod: TimelineModuleLike<S>,
  spec: SimulationSpec,
): string[] {
  const loi: string[] = [];
  const tl = mod.timeline;
  if (!tl) return loi;
  const s0 = mod.init(spec);
  const n = tl.stepCount(s0);
  if (tl.currentStep(tl.goToStep(s0, -5)) !== 0) loi.push("lùi quá đầu không kẹp về 0");
  if (tl.currentStep(tl.goToStep(s0, n + 5)) !== n - 1) loi.push("tiến quá cuối không kẹp về khung cuối");
  return loi;
}
