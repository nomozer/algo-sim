import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { makeAlgorithmModule } from "./index";
import { AlgorithmInspector, AlgorithmWorkspace } from "./ui";
import { activeTrace, type AlgorithmSimState } from "./model";
import { ALGORITHM_IDS, type AlgorithmId } from "../../../core/types";
import { POSITION_VARS } from "../../../core/pseudocode";

/**
 * W4B-2D §4 — MỘT HỆ ĐẾM VỊ TRÍ, KHÔNG PHẢI HAI.
 *
 * SỰ CỐ ĐƯỢC KHOÁ Ở ĐÂY (đo trong Chrome, artifact
 * `docs/evaluation/m17/w4b2d-search-family/position-numbering/`): trên CÙNG một
 * màn hình `binary_search`, mã giả viết `trái ← 1`, chip BIẾN viết `trái 0`,
 * vùng hành động viết `vùng xét 1–10`, nhãn cột viết `0…9`. Học sinh lần theo
 * mã giả tính `giữa ← (trái + phải) div 2` ra **5**, còn app hiện **4**.
 *
 * Vì sao KHÔNG có test nào bắt được: `algorithms.ts::pos()` đã chốt luật
 * "vị trí nói với học sinh luôn đếm từ 1" và áp cho THUYẾT MINH, nhưng chưa ai
 * viết ràng buộc giữa thuyết minh và hai bề mặt in giá trị THÔ (`VarsView`,
 * `ArrayView`). Suite 998 test vẫn xanh trong khi hai hệ đếm cùng tồn tại —
 * đúng loại lỗi im lặng mà `ARCHITECTURE_MAP §8` #11 mô tả.
 *
 * BA TẦNG KHOÁ, cố ý không gộp:
 *  1. hợp đồng `POSITION_VARS` không được lệch khỏi engine (chống CỘNG HAI LẦN);
 *  2. mỗi bề mặt riêng lẻ đếm từ 1;
 *  3. các bề mặt ĐỒNG THỜI hiện phải nói CÙNG một con số.
 * Tầng 3 mới là bất biến thật; tầng 1–2 để khi đỏ thì biết ngay hỏng ở đâu.
 */

function build(algorithmId: AlgorithmId, data: Record<string, unknown>) {
  const mod = makeAlgorithmModule(algorithmId);
  const r = mod.validateConfig({
    problem: {}, algorithm_id: algorithmId, data, data_generated: false, notes: null,
  });
  if (!r.ok) throw new Error(r.error);
  return { mod, config: r.config, state: mod.init(r.config) as AlgorithmSimState };
}

const at = (s: AlgorithmSimState, cursor: number): AlgorithmSimState => ({ ...s, cursor });

/**
 * SSR chèn `<!-- -->` giữa hai biểu thức JSX liền nhau, nên `{l+1}–{r+1}` ra
 * `1<!-- -->–<!-- -->4`. Bỏ dấu ngăn đó đi để test so ĐÚNG THỨ HỌC SINH ĐỌC,
 * chứ không so chi tiết cách React nối chuỗi.
 */
const seen = (html: string) => html.replaceAll("<!-- -->", "");

/**
 * Chip BIẾN đọc theo CẶP NHÃN–GIÁ TRỊ, không theo số trần.
 *
 * Bản đầu của test này assert `toContain(">1</span>")` và lượt TIÊM LỖI cho thấy
 * nó vô dụng: bỏ `trai` khỏi khai báo mà test vẫn xanh, vì `>1</span>` khớp
 * trúng một chip khác trên cùng panel. Một guard khớp nhầm chỗ là một guard
 * không tồn tại (`ARCHITECTURE_MAP §8` #14). Nay khớp đúng cấu trúc `VarsView`
 * dựng: nhãn rồi tới ô giá trị `font-weight:600`.
 */
function chips(panelHtml: string): Record<string, string> {
  const out: Record<string, string> = {};
  const re = />([^<>]+)<\/span><span style="font-weight:600[^"]*">([^<]*)<\/span>/g;
  for (const m of seen(panelHtml).matchAll(re)) out[m[1].trim()] = m[2].trim();
  return out;
}

const DATA: Record<AlgorithmId, Record<string, unknown>> = {
  find_max: { array: [4, 9, 2, 7], order: "asc" },
  find_min: { array: [4, 9, 2, 7], order: "asc" },
  sum_if: { array: [4, 9, 2, 7], condition: { op: ">=", value: 7 } },
  count_if: { array: [4, 9, 2, 7], condition: { op: ">=", value: 7 } },
  linear_search: { array: [4, 9, 2, 7], target: 2 },
  binary_search: { array: [2, 4, 7, 9], target: 7 },
  bubble_sort: { array: [4, 9, 2, 7], order: "asc" },
  insertion_sort: { array: [4, 9, 2, 7], order: "asc" },
  selection_sort: { array: [4, 9, 2, 7], order: "asc" },
};

/* ── 1. HỢP ĐỒNG: KHAI BÁO KHÔNG ĐƯỢC LỆCH KHỎI ENGINE ─────────────────────── */

describe("W4B-2D §4 · POSITION_VARS khớp với thứ engine thật sự ghi", () => {
  it("mọi biến được khai đều CÓ THẬT trong vars của bài đó", () => {
    for (const id of ALGORITHM_IDS) {
      const declared = POSITION_VARS[id];
      if (declared.length === 0) continue;
      const { state } = build(id, DATA[id]);
      const seen = new Set<string>();
      for (const st of activeTrace(state).steps) {
        for (const k of Object.keys(st.snapshot.vars)) seen.add(k);
      }
      for (const name of declared) {
        expect(seen.has(name), `${id}: khai "${name}" nhưng engine không ghi biến này`).toBe(true);
      }
    }
  });

  /* CÁI BẪY CHÍNH CỦA WAVE NÀY. `luot` (nổi bọt) và `vi_tri_cuc_tri` (chọn) NGHE
     như chỉ số nhưng engine đã ghi 1-based sẵn (`setVar("luot", i + 1)`). Khai
     nhầm chúng là cộng 1 lần thứ hai — sai câm, không test nào khác bắt được. */
  it("biến engine ĐÃ ghi 1-based thì KHÔNG được khai (chống cộng hai lần)", () => {
    for (const name of ["luot", "vi_tri_cuc_tri"]) {
      for (const id of ALGORITHM_IDS) {
        expect(
          POSITION_VARS[id].includes(name),
          `${id}: "${name}" đã 1-based ở engine — khai vào POSITION_VARS là +1 hai lần`,
        ).toBe(false);
      }
    }
  });

  it("mọi giá trị được khai đều nằm trong [0, n) — đúng dạng chỉ số 0-based", () => {
    for (const id of ALGORITHM_IDS) {
      const declared = POSITION_VARS[id];
      if (declared.length === 0) continue;
      const { config, state } = build(id, DATA[id]);
      const n = (config.data.array as number[]).length;
      for (const st of activeTrace(state).steps) {
        for (const name of declared) {
          const v = st.snapshot.vars[name];
          if (typeof v !== "number") continue;
          expect(v >= 0 && v < n, `${id}.${name} = ${v} không phải chỉ số 0-based của dãy dài ${n}`)
            .toBe(true);
        }
      }
    }
  });
});

/* ── 2. TỪNG BỀ MẶT ĐẾM TỪ 1 ────────────────────────────────────────────────── */

describe("W4B-2D §4 · từng bề mặt đếm từ 1", () => {
  it("nhãn cột sân khấu chạy 1..n, không bao giờ có cột 0", () => {
    const { config, state } = build("find_max", DATA.find_max);
    const h = renderToString(
      <AlgorithmWorkspace config={config} state={state} busy={false} dispatch={() => {}} />,
    );
    const svg = h.slice(h.indexOf('aria-label="Mô phỏng dãy số"'));
    const n = (config.data.array as number[]).length;
    for (let i = 1; i <= n; i += 1) {
      expect(svg, `thiếu nhãn cột ${i}`).toContain(`>${i}</text>`);
    }
    expect(svg, "còn nhãn cột 0 — hệ đếm của mã lọt lên sân khấu").not.toContain(">0</text>");
  });

  it("chip BIẾN của biến vị trí hiện giá trị engine + 1", () => {
    const { config, state } = build("binary_search", DATA.binary_search);
    // Bước đầu tiên có đủ trai/phai/giua.
    const steps = activeTrace(state).steps;
    const k = steps.findIndex((s) => typeof s.snapshot.vars["giua"] === "number");
    expect(k, "fixture không tới được bước có `giữa`").toBeGreaterThanOrEqual(0);
    const s = at(state, k);
    const vars = steps[k].snapshot.vars;
    const h = renderToString(
      <AlgorithmInspector config={config} state={s} busy={false} dispatch={() => {}} />,
    );
    const c = chips(h);
    for (const [name, label] of [["trai", "trái"], ["phai", "phải"], ["giua", "giữa"]] as const) {
      const raw = vars[name] as number;
      expect(c[label], `chip ${label} phải hiện ${raw + 1}`).toBe(String(raw + 1));
    }
  });

  /* Mặc định an toàn: không khai gì thì không đổi gì — đây là thứ giữ cho
     `program-module` (tên biến do ĐỀ BÀI đặt) không bị cộng nhầm. */
  it("bài không khai biến vị trí thì chip giữ nguyên giá trị engine", () => {
    const { config, state } = build("bubble_sort", DATA.bubble_sort);
    const steps = activeTrace(state).steps;
    const k = steps.findIndex((s) => typeof s.snapshot.vars["luot"] === "number");
    expect(k).toBeGreaterThanOrEqual(0);
    const raw = steps[k].snapshot.vars["luot"] as number;
    const h = renderToString(
      <AlgorithmInspector config={config} state={at(state, k)} busy={false} dispatch={() => {}} />,
    );
    expect(chips(h)["lượt"], `lượt phải giữ ${raw}, không thành ${raw + 1}`).toBe(String(raw));
  });

  it("không còn định danh kĩ thuật snake_case nào lọt lên chip BIẾN", () => {
    for (const id of ALGORITHM_IDS) {
      const { config, state } = build(id, DATA[id]);
      for (const [k] of activeTrace(state).steps.entries()) {
        const h = renderToString(
          <AlgorithmInspector config={config} state={at(state, k)} busy={false} dispatch={() => {}} />,
        );
        expect(h, `${id} bước ${k}: chip mang định danh kĩ thuật`).not.toMatch(/>[a-z]+_[a-z_]+</);
      }
    }
  });
});

/* ── 3. BẤT BIẾN THẬT: CÁC BỀ MẶT ĐỒNG THỜI PHẢI NÓI CÙNG MỘT SỐ ───────────── */

describe("W4B-2D §4 · cùng màn hình ⇒ cùng một con số", () => {
  /** Bước cam kết đầu tiên — nơi vùng hành động và chip BIẾN cùng hiện. */
  const firstSearchStep = (state: AlgorithmSimState) =>
    activeTrace(state).steps.findIndex((s) =>
      s.events.some((e) => e.type === "compare_value") ||
      typeof s.snapshot.vars["giua"] === "number");

  it("linear_search: chip `i`, vùng hành động và nhãn cột nói cùng một vị trí", () => {
    const { config, state } = build("linear_search", DATA.linear_search);
    const k = firstSearchStep(state);
    expect(k).toBeGreaterThanOrEqual(0);
    const s = at(state, k);
    const i = activeTrace(state).steps[k].snapshot.vars["i"] as number;

    const stage = renderToString(
      <AlgorithmWorkspace config={config} state={s} busy={false} dispatch={() => {}} />,
    );
    const panel = renderToString(
      <AlgorithmInspector config={config} state={s} busy={false} dispatch={() => {}} />,
    );

    // Vùng hành động đã nói "vị trí i+1" từ trước wave này — nó là mốc ĐÚNG.
    expect(seen(stage), "vùng hành động đổi cách đếm").toContain(`Phần tử vị trí ${i + 1}`);
    // Chip BIẾN phải nói CÙNG con số đó, không phải giá trị thô.
    expect(chips(panel)["i"], `chip i phải là ${i + 1}, không phải ${i}`).toBe(String(i + 1));
    // Và nhãn cột tương ứng cũng vậy.
    expect(stage).toContain(`>${i + 1}</text>`);
  });

  it("binary_search: vùng xét của vùng hành động khớp chip trái/phải", () => {
    const { config, state } = build("binary_search", DATA.binary_search);
    const k = firstSearchStep(state);
    expect(k).toBeGreaterThanOrEqual(0);
    const s = at(state, k);
    const v = activeTrace(state).steps[k].snapshot.vars;
    const l = v["trai"] as number;
    const r = v["phai"] as number;

    const stage = renderToString(
      <AlgorithmWorkspace config={config} state={s} busy={false} dispatch={() => {}} />,
    );
    const panel = renderToString(
      <AlgorithmInspector config={config} state={s} busy={false} dispatch={() => {}} />,
    );

    expect(seen(stage), "vùng xét đổi cách đếm").toContain(`${l + 1}–${r + 1}`);
    const c = chips(panel);
    expect(c["trái"], `chip trái phải là ${l + 1}`).toBe(String(l + 1));
    expect(c["phải"], `chip phải phải là ${r + 1}`).toBe(String(r + 1));
  });

  /* PHÉP ĐO PHẢI THẬT SỰ ĐO. Nếu bỏ khai báo đi thì test trên PHẢI đỏ — guard
     chưa từng thấy màu đỏ là guard chưa được chứng minh (ARCHITECTURE_MAP §8
     #14). Ở đây tiêm lỗi bằng cách hiển thị với khai báo RỖNG. */
  it("tiêm lỗi: bỏ khai báo vị trí thì mâu thuẫn quay lại (guard đỏ được)", () => {
    const { config, state } = build("binary_search", DATA.binary_search);
    const k = firstSearchStep(state);
    const s = at(state, k);
    const l = activeTrace(state).steps[k].snapshot.vars["trai"] as number;

    const withDecl = renderToString(
      <AlgorithmInspector config={config} state={s} busy={false} dispatch={() => {}} />,
    );
    // `trai` = 0 ở bước đầu ⇒ bản KHÔNG khai in "0", bản có khai in "1". Nhờ
    // chênh lệch đó, lượt tiêm lỗi (bỏ "trai" khỏi POSITION_VARS) làm ĐỎ cả test
    // này LẪN test đối chiếu ở trên — đã chạy thật để xác nhận.
    expect(l, "fixture mất ý nghĩa nếu trái != 0 ở bước đầu").toBe(0);
    expect(POSITION_VARS.binary_search).toContain("trai");
    expect(chips(withDecl)["trái"]).toBe("1");
  });
});
