/**
 * action-probe.ts — HỌC SINH CÓ ĐƯỜNG NÀO ĐỔI ĐẦU VÀO CỦA BÀI NÀY KHÔNG?
 *
 * ─── VÌ SAO PHẢI CÓ MỘT CHỦ SỞ HỮU ────────────────────────────────────────
 *
 * Câu hỏi trên được hỏi ở HAI nơi: cổng thường trực offline
 * (`experience-gate.test.ts`) và bản chứng nhận trên trình duyệt
 * (`scripts/certify-experience-w12.mjs`). Để hai nơi tự viết lấy là tái lập
 * đúng lỗi vừa sửa ở `tool-affordance.ts` — một luật chép tay ba lần thì sai ba
 * lần và không có chỗ nào để sửa một lần.
 *
 * ─── VÌ SAO KHÔNG ĐƯỢC ĐOÁN TÊN ───────────────────────────────────────────
 *
 * Bộ này đã sai BA lần trong W12, và cả ba đều đánh giá THẤP sản phẩm — vì một
 * action sai hình dạng KHÔNG ném lỗi, nó bị `module.apply` trả về state cũ,
 * đọc ra y hệt "bài này không tương tác được":
 *
 *   `whatif_swap {from,to}`  → thật là `{i,j}`            (types.ts)
 *   `toggle {id}`            → thật là `{target}`          (types.ts)
 *   `set_param 'decimalValue'` → thật là `'decimal'`       (binary/index.ts)
 *   `links: [{a,b}]`          → cũng có dạng `[[a,b]]`     (network/model.ts)
 *
 * Bài học ghi lại ở đây vì đây là chỗ người sau sẽ thêm target mới: **tên
 * action nằm trong `module.apply`, KHÔNG suy được từ tên field trong config.**
 * Thêm ứng viên thì mở đúng module ra đọc.
 */
import type { SimAction } from "./types";

/** Config nào cũng chỉ là dữ liệu — đọc dò, không ép kiểu theo miền. */
type AnyConfig = Record<string, unknown>;

const num = (v: unknown): v is number => typeof v === "number";
const str = (v: unknown): v is string => typeof v === "string";
const arr = (v: unknown): v is unknown[] => Array.isArray(v);
const obj = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v);

const VARIANT_ALT: Record<string, string> = {
  bfs: "dfs", dfs: "bfs",
  preorder: "inorder", inorder: "postorder", postorder: "preorder",
};

/**
 * Mọi action mà HỌC SINH có thể phát ở bài này, dẫn từ chính config đã validate.
 *
 * Mỗi ứng viên chỉ dựng khi field tương ứng CÓ MẶT — không bắn bừa một danh
 * sách cố định, vì "bị từ chối" và "không áp dụng được" là hai chuyện khác nhau
 * và gộp lại sẽ làm mọi bài trông như có tương tác.
 */
export function candidateActions(config: unknown): SimAction[] {
  const cfg: AnyConfig = obj(config) ? config : {};
  const data: AnyConfig = obj(cfg.data) ? cfg.data : {};
  const out: SimAction[] = [];

  const cond = obj(data.condition) ? data.condition : null;
  if (cond && num(cond.value)) {
    out.push({ type: "set_param", name: "condition.value", value: cond.value + 1 });
  }
  if (arr(data.array) && data.array.length > 1) {
    out.push({ type: "whatif_swap", i: 0, j: 1 });
  }
  if (str(cfg.variant) && VARIANT_ALT[cfg.variant]) {
    out.push({ type: "set_param", name: "variant", value: VARIANT_ALT[cfg.variant] });
  }
  if (arr(cfg.nodes) && cfg.nodes.length > 1 && str(cfg.start)) {
    const other = cfg.nodes.find((n) => obj(n) && n.id !== cfg.start);
    if (obj(other) && str(other.id)) {
      out.push({ type: "set_param", name: "start", value: other.id });
    }
  }
  if (arr(cfg.links) && cfg.links.length) {
    /* HAI HÌNH DẠNG, và bản đầu chỉ biết một. `network.packet_routing` khai liên
       kết là MẢNG CẶP `["client","router"]`, không phải object `{a,b}` — nên
       phép kiểm `l.a && l.b` trượt, không sinh ứng viên nào, và bản soát ghi
       target này là "không đổi được đầu vào".
       Dò tay trên trình duyệt: bấm một vùng ngắt liên kết ⇒ links 3→2 và
       route → [] (không tới được). Sản phẩm ĐÚNG, phép đo SAI — lần thứ TƯ
       cùng một họ lỗi trong wave này (xem đầu file). */
    const l = cfg.links[0];
    if (obj(l) && str(l.a) && str(l.b)) {
      out.push({ type: "net_disconnect", a: l.a, b: l.b });
    } else if (arr(l) && l.length >= 2 && str(l[0]) && str(l[1])) {
      out.push({ type: "net_disconnect", a: l[0], b: l[1] });
    }
  }
  if (arr(cfg.inputs) && cfg.inputs.length) {
    const first = cfg.inputs[0];
    if (obj(first) && str(first.id)) out.push({ type: "toggle", target: first.id });
  }
  if (str(cfg.text) && cfg.text.length) {
    out.push({ type: "set_param", name: "text", value: cfg.text + "a" });
  }
  if (str(cfg.encoding)) {
    out.push({ type: "set_param", name: "encoding", value: cfg.encoding === "ascii" ? "utf8" : "ascii" });
  }
  if (arr(cfg.schema) && cfg.schema.length) {
    const col = cfg.schema[0];
    if (obj(col) && str(col.name)) {
      out.push({ type: "set_param", name: "filter.column", value: col.name });
    }
  }
  if (obj(cfg.style)) {
    const k = Object.keys(cfg.style)[0];
    if (k) out.push({ type: "set_param", name: k, value: "#123456" });
  }
  if (str(cfg.inputValue) || num(cfg.inputValue)) {
    out.push({ type: "set_param", name: "inputValue", value: String(cfg.inputValue) === "1" ? "10" : "1" });
  }
  if (num(cfg.targetBase)) {
    out.push({ type: "set_param", name: "targetBase", value: cfg.targetBase === 2 ? 8 : 2 });
  }
  /* Bài mạch logic khai công tắc bằng CHỮ CỐ ĐỊNH trong renderer (`logic/ui.tsx`
     dispatch target 'A'/'B'), không lấy từ config — nên không dò ra được. */
  if (cfg.inputA !== undefined || cfg.gate !== undefined) {
    out.push({ type: "toggle", target: "A" });
    out.push({ type: "toggle", target: "B" });
  }
  if (arr(cfg.objects) && cfg.objects.length) {
    const o = cfg.objects[0];
    if (obj(o) && str(o.id)) {
      out.push({ type: "toggle", target: o.id });
      out.push({ type: "move", target: o.id, x: 50, y: 50 });
    }
  }
  /* `decimalValue` là tên FIELD; tên ACTION là `decimal` — xem đầu file. */
  if (num(cfg.decimalValue)) {
    out.push({ type: "toggle", target: "0" });
    out.push({ type: "set_param", name: "decimal", value: cfg.decimalValue + 1 });
  }
  if (num(cfg.value)) {
    out.push({ type: "set_param", name: "value", value: cfg.value + 1 });
  }
  return out;
}
