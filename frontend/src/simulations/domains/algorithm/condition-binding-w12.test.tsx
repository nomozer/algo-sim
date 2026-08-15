import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { getSimulation, listSimulations } from "../../registry";
import { registerAllSimulations } from "../../index";
import { AlgorithmWorkspace } from "./ui";
import type { AlgorithmConfig, AlgorithmSimState } from "./model";

/**
 * BỀ MẶT ĐIỀU KHIỂN PHẢI SOI ĐÚNG ENGINE, KHÔNG SOI ĐỀ GỐC.
 *
 * ─── LỖI CÓ THẬT, BẮT TRÊN MÀN HÌNH NGƯỜI DÙNG ───────────────────────────
 *
 * `store.dispatch` chỉ thay `active.state`; `active.config` ĐÔNG CỨNG có chủ
 * đích (để `specDrift` biết mô hình đã rời khỏi đề chưa). Nhưng `set_param`
 * ghi điều kiện mới vào `state.config` — và ĐÓ là thứ engine dùng để chấm.
 *
 * `ConditionBar` trước đây đọc prop `config`, tức bản đông cứng. Hệ quả đo
 * được:
 *
 *   học sinh chọn ">"   → engine dùng ">"   → ô chọn nhảy về ">=" của đề gốc
 *   thử thách hỏi "80 có được cộng vào tổng không?"
 *   màn hình nói  "Phép so sánh: lớn hơn hoặc bằng · Ngưỡng 80"
 *   engine chấm   80 > 80 = Sai
 *
 * Ai trả lời theo thứ NHÌN THẤY ĐƯỢC (80 ≥ 80 ⇒ cộng vào tổng) bị chấm SAI.
 * Đây là lỗi đúng đắn, không phải lỗi thẩm mỹ: engine là nơi DUY NHẤT có thẩm
 * quyền phán đúng/sai, nên bề mặt không được nói khác nó.
 */

function sumIfState(): { config: AlgorithmConfig; state: AlgorithmSimState } {
  if (listSimulations().length === 0) registerAllSimulations();
  const mod = getSimulation("algorithm.sum_if")!;
  const sample = {
    algorithm_id: "sum_if",
    data: { array: [45, 120, 80, 30, 95], condition: { op: ">=", value: 80 } },
  } as unknown as AlgorithmConfig;
  const v = mod.validateConfig(sample);
  if (!v.ok) throw new Error("fixture không qua validate — sửa fixture, đừng nới validator");
  const config = v.config as AlgorithmConfig;
  return { config, state: mod.init(config) as AlgorithmSimState };
}

const html = (config: AlgorithmConfig, state: AlgorithmSimState) =>
  renderToString(
    <AlgorithmWorkspace config={config} state={state} busy={false} dispatch={() => {}} />,
  );

/** Phép so sánh ĐANG ĐƯỢC CHỌN, đọc từ HTML thật.
 *  SSR của React đặt `selected` lên `<option>` (không đặt `value` lên `<select>`)
 *  và escape `>` thành `&gt;` — đọc sai chỗ này thì test xanh/đỏ vì lý do sai. */
function selectedOp(out: string): string | null {
  const m = out.match(/<option value="([^"]*)" selected/);
  return m ? m[1].replace(/&gt;/g, ">").replace(/&lt;/g, "<") : null;
}

describe("W12 — thanh điều kiện phải hiện GIÁ TRỊ ENGINE ĐANG DÙNG", () => {
  it("KIỂM SOÁT DƯƠNG TÍNH — chưa đổi gì thì hai nguồn trùng nhau", () => {
    const { config, state } = sumIfState();
    expect(state.config.data.condition!.op).toBe(">=");
    expect(selectedOp(html(config, state))).toBe(">=");
  });

  it("đổi phép so sánh xong, ô chọn phải theo ENGINE chứ không quay về đề gốc", () => {
    const { config, state } = sumIfState();
    const mod = getSimulation("algorithm.sum_if")!;
    const after = mod.apply(state, { type: "set_param", name: "condition.op", value: ">" }) as AlgorithmSimState;

    /* Tiền đề của phép đo: engine THẬT SỰ đã đổi. Không có khẳng định này thì
       test vẫn xanh khi `apply` im lặng không làm gì. */
    expect(after, "apply trả lại state cũ — set_param không tới engine").not.toBe(state);
    expect(after.config.data.condition!.op).toBe(">");
    expect(config.data.condition!.op, "đề gốc phải giữ nguyên — specDrift dựa vào nó").toBe(">=");

    /* `config` truyền vào vẫn là bản ĐÔNG CỨNG, đúng như store làm thật. */
    expect(selectedOp(html(config, after)), "ô chọn vẫn hiện phép so sánh của ĐỀ GỐC")
      .toBe(">");
  });

  it("đổi ngưỡng cũng vậy — thanh trượt không được kẹt ở giá trị đề gốc", () => {
    const { config, state } = sumIfState();
    const mod = getSimulation("algorithm.sum_if")!;
    const after = mod.apply(state, { type: "set_param", name: "condition.value", value: 95 }) as AlgorithmSimState;
    expect(after).not.toBe(state);
    expect(after.config.data.condition!.value).toBe(95);
    expect(html(config, after)).toContain('value="95"');
  });
});
