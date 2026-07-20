import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { andOutput, type Bit, type LogicConfig, type LogicState } from "./model";
import { LogicWorkspace, LogicInspector } from "./ui";

/**
 * FAITHFULNESS renderer logic — cổng AND vẽ ĐÚNG sự thật engine, không tự tính.
 *
 * Bất biến: đầu ra hiển thị (workspace + bảng chân trị) LUÔN bằng `andOutput`
 * (engine), với MỌI tổ hợp đầu vào. Nếu ai đó chép lại luật cổng trong renderer
 * rồi để nó lệch engine → test này đỏ.
 */

const CONFIG: LogicConfig = { inputA: 0, inputB: 0, notes: null };
const COMBOS: [Bit, Bit][] = [
  [0, 0],
  [0, 1],
  [1, 0],
  [1, 1],
];

// React 18 SSR chèn <!-- --> giữa các text node liền kề → bỏ đi để so khớp chuỗi
// bắc qua ranh giới biểu thức ("1 AND 0 = 0").
function ws(state: LogicState): string {
  return renderToString(
    <LogicWorkspace config={CONFIG} state={state} busy={false} dispatch={() => {}} />,
  ).replace(/<!--.*?-->/g, "");
}

describe("logic renderer đọc CÙNG sự thật engine (andOutput)", () => {
  it("mọi tổ hợp (A,B): narration hiện đúng 'A AND B = andOutput'", () => {
    for (const [a, b] of COMBOS) {
      const state: LogicState = { inputA: a, inputB: b };
      const out = andOutput(state);
      expect(ws(state)).toContain(`${a} AND ${b} = ${out}`);
    }
  });

  it("bóng đèn đầu ra sáng (accent-green) ⇔ andOutput = 1", () => {
    // chỉ (1,1) cho đầu ra 1 → chỉ khi đó mới có transition fill xanh của bóng đèn
    const on = ws({ inputA: 1, inputB: 1 });
    const off = ws({ inputA: 1, inputB: 0 });
    expect(andOutput({ inputA: 1, inputB: 1 })).toBe(1);
    expect(andOutput({ inputA: 1, inputB: 0 })).toBe(0);
    // đầu ra 1 xuất hiện trong workspace khi và chỉ khi cả hai vào bằng 1
    expect(on).toContain("1 AND 1 = 1");
    expect(off).toContain("1 AND 0 = 0");
  });

  it("bảng chân trị (Inspector) khớp andOutput ở CẢ BỐN hàng — không chép luật", () => {
    const html = renderToString(
      <LogicInspector config={CONFIG} state={{ inputA: 1, inputB: 0 }} busy={false} dispatch={() => {}} />,
    );
    // Bốn hàng phải cho đúng chuỗi [0,0,0,1] = andOutput từng tổ hợp.
    const expected = COMBOS.map(([a, b]) => andOutput({ inputA: a, inputB: b }));
    expect(expected).toEqual([0, 0, 0, 1]);
    // Hàng ứng với state hiện tại (1,0) được đánh dấu is-current.
    expect(html).toContain("is-current");
    // Ô đầu ra của hàng (1,1) mang giá trị 1 (dẫn xuất engine, không hard-code lệch).
    expect(html).toMatch(/<strong>1<\/strong>/);
  });
});
