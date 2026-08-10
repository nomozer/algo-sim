import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { makeAlgorithmModule } from "./index";
import { AlgorithmWorkspace } from "./ui";
import { accumulatorViewOf } from "./decision";
import type { AlgorithmId } from "../../../core/types";
import type { AlgorithmSimState } from "./model";

/**
 * W4B-2U2 §12 — CHUYỂN TIẾP CỦA BIẾN TÍCH LUỸ PHẢI THẤY ĐƯỢC.
 *
 * Khoảng trống cuối cùng của ngữ pháp thị giác (audit U2-A xếp `count_if`/
 * `sum_if` là TRANSITION = `TEXT_ONLY`): biến đếm/tổng chỉ sống trong vùng hành
 * động, nên `4 → 5` phải đọc chữ mới biết.
 *
 * Bất biến có HAI vế, và vế hai mới là vế giữ tính trung thực:
 *   1. giá trị đổi ⇒ sân khấu hiện TRƯỚC → SAU;
 *   2. giá trị "trước" đến từ bước ĐÃ QUA, **không bao giờ** từ bước sau — nhìn
 *      tới `cursor + 1` là lộ đáp án của chính điểm quyết định đang hỏi.
 */

const DATA: Partial<Record<AlgorithmId, Record<string, unknown>>> = {
  count_if: { array: [4, 9, 2, 7, 5, 8], condition: { op: ">=", value: 7 } },
  sum_if: { array: [4, 9, 2, 7, 5, 8], condition: { op: ">=", value: 7 } },
  find_max: { array: [4, 9, 2, 7, 5, 8] },
  find_min: { array: [4, 9, 2, 7, 5, 8] },
};

function build(id: AlgorithmId) {
  const mod = makeAlgorithmModule(id);
  const r = mod.validateConfig({
    problem: {}, algorithm_id: id, data: DATA[id]!, data_generated: false, notes: null,
  });
  if (!r.ok) throw new Error(`${id}: ${r.error}`);
  return { mod, config: r.config, state: mod.init(r.config) as AlgorithmSimState };
}
const at = (s: AlgorithmSimState, cursor: number): AlgorithmSimState => ({ ...s, cursor });

const html = (id: AlgorithmId, cursor: number) => {
  const b = build(id);
  return renderToString(
    <AlgorithmWorkspace config={b.config} state={at(b.state, cursor)} busy={false} dispatch={() => {}} />,
  );
};

const SCAN: AlgorithmId[] = ["count_if", "sum_if", "find_max", "find_min"];

describe("W4B-2U2 · biến tích luỹ sống trên SÂN KHẤU", () => {
  it("mọi bài quét dãy đều có biến tích luỹ đọc được từ engine", () => {
    for (const id of SCAN) {
      const { state } = build(id);
      const acc = accumulatorViewOf(at(state, 1));
      expect(acc, `${id}: không đọc được biến tích luỹ`).not.toBeNull();
      expect(acc!.label.length).toBeGreaterThan(0);
    }
  });

  it("bài KHÔNG có biến tích luỹ ⇒ null (không bịa huy hiệu)", () => {
    const { state } = build("find_max");
    const other = { ...state, config: { ...state.config, algorithm_id: "binary_search" } };
    expect(accumulatorViewOf(other as AlgorithmSimState)).toBeNull();
  });

  it("bước đầu: chưa có 'trước' ⇒ không dựng mũi tên chuyển tiếp", () => {
    for (const id of SCAN) {
      const { state } = build(id);
      const acc = accumulatorViewOf(at(state, 0))!;
      expect(acc.previous, `${id}`).toBeNull();
      expect(acc.changed, `${id}`).toBe(false);
    }
  });

  it("có ÍT NHẤT một bước mà giá trị đổi ⇒ chuyển tiếp hiện ra", () => {
    for (const id of SCAN) {
      const { state } = build(id);
      const total = state.trace.steps.length;
      const changed = [...Array(total).keys()]
        .map((k) => accumulatorViewOf(at(state, k))!)
        .filter((a) => a.changed);
      expect(changed.length, `${id}: không bước nào thấy được chuyển tiếp`).toBeGreaterThan(0);
      for (const a of changed) {
        expect(a.previous, `${id}`).not.toBeNull();
        expect(a.previous).not.toBe(a.value);
      }
    }
  });

  it("KHÔNG NHÌN BƯỚC SAU — 'trước' luôn khớp giá trị của bước liền trước", () => {
    /* Vế chống-lộ-đáp-án. Một bản cài đặt đọc `cursor + 1` để lấy "sau" sẽ đỏ ở
       đây, và đó đúng là thứ `decisionPointOf` giữ kín. */
    for (const id of SCAN) {
      const { state } = build(id);
      for (let k = 1; k < state.trace.steps.length; k += 1) {
        const acc = accumulatorViewOf(at(state, k))!;
        const prevAcc = accumulatorViewOf(at(state, k - 1))!;
        expect(acc.previous, `${id}@${k}`).toBe(prevAcc.value);
      }
    }
  });
});

describe("W4B-2U2 · huy hiệu nằm TRÊN sân khấu, không phải một tấm thẻ khác", () => {
  it("count_if: sân khấu in cả giá trị trước lẫn sau ở bước có thay đổi", () => {
    const { state } = build("count_if");
    const k = [...Array(state.trace.steps.length).keys()]
      .find((i) => accumulatorViewOf(at(state, i))!.changed)!;
    const acc = accumulatorViewOf(at(state, k))!;
    const out = html("count_if", k);
    expect(out).toContain("acc-badge");
    expect(out).toContain("is-changed");
    expect(out, "mất giá trị TRƯỚC ⇒ học sinh không thấy chuyển tiếp")
      .toContain(`>${acc.previous}<`);
    expect(out).toContain(`>${acc.value}<`);
  });

  it("sum_if: cùng một chủ sở hữu, không phải bản cài đặt thứ hai", () => {
    const { state } = build("sum_if");
    const k = [...Array(state.trace.steps.length).keys()]
      .find((i) => accumulatorViewOf(at(state, i))!.changed)!;
    const acc = accumulatorViewOf(at(state, k))!;
    const out = html("sum_if", k);
    expect(out).toContain("acc-badge");
    expect(out).toContain(`>${acc.previous}<`);
    expect(out).toContain(`>${acc.value}<`);
  });

  it("huy hiệu nằm TRONG `.sim-stage` — trạng thái cạnh đối tượng nó mô tả", () => {
    const { state } = build("count_if");
    const k = [...Array(state.trace.steps.length).keys()]
      .find((i) => accumulatorViewOf(at(state, i))!.changed)!;
    const out = html("count_if", k);
    const stage = out.indexOf('class="sim-stage"');
    const badge = out.indexOf("acc-badge");
    const stageEnd = out.indexOf("stage-legend");
    expect(stage).toBeGreaterThan(-1);
    expect(badge, "huy hiệu rơi ra ngoài sân khấu").toBeGreaterThan(stage);
    expect(badge).toBeLessThan(stageEnd);
  });
});
