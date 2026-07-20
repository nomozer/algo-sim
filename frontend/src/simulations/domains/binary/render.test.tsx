import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import {
  binaryString,
  decimalOf,
  placeValues,
  type BinaryConfig,
  type BinaryState,
} from "./model";
import { BinaryWorkspace, BinaryInspector } from "./ui";

/**
 * FAITHFULNESS renderer binary — bit/thập phân/trọng số vẽ ĐÚNG sự thật engine.
 *
 * Bất biến: giá trị thập phân hiển thị LUÔN bằng `decimalOf(state)` (tổng trọng
 * số các bit đang bật) — renderer KHÔNG tự cộng theo cách riêng. Số ô bit = số
 * bit trong state. Đổi bit → giá trị hiển thị đổi theo engine.
 */

const CONFIG: BinaryConfig = { decimalValue: 0, bitWidth: 4, notes: null };

// Một vài trạng thái có giá trị tính TAY để bắt lỗi lệch: 1011=11, 0000=0, 1111=15.
const CASES: { bits: BinaryState["bits"]; dec: number; bin: string }[] = [
  { bits: [1, 0, 1, 1], dec: 11, bin: "1011" },
  { bits: [0, 0, 0, 0], dec: 0, bin: "0000" },
  { bits: [1, 1, 1, 1], dec: 15, bin: "1111" },
];

// React 18 SSR chèn <!-- --> giữa text node liền kề → bỏ đi để so khớp
// "= 11 (hệ thập phân)" bắc qua ranh giới biểu thức.
function ws(state: BinaryState): string {
  return renderToString(
    <BinaryWorkspace config={CONFIG} state={state} busy={false} dispatch={() => {}} />,
  ).replace(/<!--.*?-->/g, "");
}

describe("binary renderer đọc CÙNG sự thật engine (decimalOf/placeValues)", () => {
  it("mọi trạng thái: engine tính đúng thập phân + workspace hiện đúng con số đó", () => {
    for (const c of CASES) {
      const state: BinaryState = { bits: c.bits, bitWidth: 4 };
      // engine đúng như tính tay
      expect(decimalOf(state)).toBe(c.dec);
      expect(binaryString(state)).toBe(c.bin);
      // renderer hiện ĐÚNG con số của engine (không tự cộng kiểu khác)
      expect(ws(state)).toContain(`= ${c.dec} (hệ thập phân)`);
      expect(ws(state)).toContain(c.bin);
    }
  });

  it("số ô bit vẽ ra = số bit trong state (không thừa/thiếu)", () => {
    const state: BinaryState = { bits: [1, 0, 1, 1], bitWidth: 4 };
    // mỗi bit là một <rect> ô bấm được; đếm rect khớp độ dài bits
    const rectCount = (ws(state).match(/<rect/g) ?? []).length;
    expect(rectCount).toBe(state.bits.length);
  });

  it("Inspector: thập phân = decimalOf và trọng số = placeValues (dẫn xuất, không hard-code)", () => {
    const state: BinaryState = { bits: [1, 0, 1, 1], bitWidth: 4 };
    const html = renderToString(
      <BinaryInspector config={CONFIG} state={state} busy={false} dispatch={() => {}} />,
    );
    expect(html).toContain(String(decimalOf(state))); // 11
    for (const pv of placeValues(4)) expect(html).toContain(String(pv)); // 8·4·2·1
  });
});
