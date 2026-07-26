import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";

import { toBase } from "./convert-module";
import {
  CharEncodingInspector,
  CharEncodingWorkspace,
  codePointsOf,
  committedRowCount,
  makeCharEncodingModule,
  runCharacterEncoding,
  validateCharEncodingSpec,
  type CharEncodingSpec,
  type CharEncodingState,
} from "./encoding-module";

/**
 * M17 W3 — engine mã hoá ký tự (FRONTEND sở hữu thực thi).
 *
 * Bất biến khoá:
 * - duyệt theo CODE POINT (`Array.from`), KHÔNG theo UTF-16 unit;
 * - emoji/surrogate bị từ chối GIỐNG backend (không sai câm giữa hai tầng);
 * - nhị phân đến từ `toBase()` của base_conversion — KHÔNG có converter thứ hai,
 *   KHÔNG tự đặt quy ước đệm số 0;
 * - bảng hiện DẦN: mã chỉ xuất hiện sau bước tra, nhị phân sau bước đổi;
 * - renderer chỉ đọc trace/rows.
 */

// ESCAPE SEQUENCE có chủ đích — viết ký tự literal thì editor có thể lặng lẽ
// chuẩn hoá và test sẽ đo cái editor chứ không đo engine.
const PRECOMPOSED = "ế";              // ế — MỘT code point
const DECOMPOSED = "ế";   // e + ◌̂ + ◌́ — BA code point
const EMOJI = "\u{1F600}";                 // 😀 — U+1F600, ngoài BMP
const LONE_SURROGATE = "\uD83D";

const spec = (over: Partial<CharEncodingSpec> = {}): unknown => ({
  spec_version: "charenc-1.0",
  text: "A",
  encoding: "ascii",
  ...over,
});

function parse(raw: unknown): CharEncodingSpec {
  const v = validateCharEncodingSpec(raw);
  if (!v.ok) throw new Error(`đáng lẽ hợp lệ nhưng bị từ chối: ${v.error}`);
  return v.spec;
}

function stateOf(raw: unknown, cursor = 0): CharEncodingState {
  const s = parse(raw);
  const run = runCharacterEncoding(s);
  return { spec: s, trace: run.trace, cursor, rows: run.rows };
}

const noop = () => {};
const workspace = (st: CharEncodingState) =>
  renderToString(<CharEncodingWorkspace state={st} config={st.spec} busy={false} dispatch={noop} />);

/* ══════════ Unicode theo CODE POINT ══════════ */

describe("duyệt theo code point, không theo UTF-16 unit", () => {
  it("chênh lệch JS/Python là THẬT — và engine phải theo code point", () => {
    expect(EMOJI.length).toBe(2);              // UTF-16 unit — cái BẪY
    expect(Array.from(EMOJI).length).toBe(1);  // code point — cái ĐÚNG
    expect(codePointsOf(EMOJI)).toEqual([0x1f600]);
  });

  it("precomposed 'ế' là MỘT code point U+1EBF", () => {
    expect(codePointsOf(PRECOMPOSED)).toEqual([0x1ebf]);
    expect(0x1ebf).toBe(7871);
  });

  it("decomposed là BA code point, KHÔNG bị gộp", () => {
    expect(codePointsOf(DECOMPOSED)).toEqual([0x0065, 0x0302, 0x0301]);
    expect(DECOMPOSED).not.toBe(PRECOMPOSED);
  });

  it("engine KHÔNG dùng text.length làm số ký tự", () => {
    const { rows } = runCharacterEncoding(parse(spec({
      text: DECOMPOSED, encoding: "unicode_codepoint",
    })));
    expect(rows).toHaveLength(3);   // 3 code point, không phải 3 UTF-16 unit tình cờ
    expect(rows.map((r) => r.codePoint)).toEqual([0x0065, 0x0302, 0x0301]);
  });
});

/* ══════════ từ chối giống backend ══════════ */

describe("từ chối cùng phạm vi với backend", () => {
  it("emoji ngoài BMP bị từ chối, KHÔNG thành hai ký tự BMP", () => {
    const v = validateCharEncodingSpec(spec({ text: EMOJI, encoding: "unicode_codepoint" }));
    expect(v.ok).toBe(false);
    if (!v.ok) expect(v.error).toContain("emoji");
  });

  it("surrogate đơn lẻ bị từ chối", () => {
    const v = validateCharEncodingSpec(spec({ text: LONE_SURROGATE, encoding: "unicode_codepoint" }));
    expect(v.ok).toBe(false);
  });

  it("ký tự ngoài ASCII ở chế độ ascii bị từ chối, KHÔNG thay bằng 'e' hay '?'", () => {
    const v = validateCharEncodingSpec(spec({ text: PRECOMPOSED, encoding: "ascii" }));
    expect(v.ok).toBe(false);
    if (!v.ok) expect(v.error).toContain("ASCII");
  });

  it("spec mang kết quả bị từ chối (R0)", () => {
    expect(validateCharEncodingSpec({ ...(spec() as object), rows: [] }).ok).toBe(false);
    expect(validateCharEncodingSpec({ ...(spec() as object), binary_values: ["1"] }).ok).toBe(false);
  });
});

/* ══════════ nhị phân đến TỪ base_conversion ══════════ */

describe("không có bộ chuyển đổi thứ hai", () => {
  it("ENC-1: 'A' → 65 → đúng bằng toBase(65, 2)", () => {
    const { rows } = runCharacterEncoding(parse(spec({ text: "A" })));
    expect(rows[0].decimal).toBe(65);
    expect(rows[0].binary).toBe(toBase(65, 2));   // KHÔNG hard-code chuỗi
  });

  it("ENC-3: ký tự '7' có mã 55 — KHÔNG phải số nguyên 7", () => {
    const { rows } = runCharacterEncoding(parse(spec({ text: "7" })));
    expect(rows[0].char).toBe("7");
    expect(rows[0].decimal).toBe(55);
    expect(rows[0].decimal).not.toBe(7);
    expect(rows[0].binary).toBe(toBase(55, 2));
  });

  it("ENC-4: 'ế' → 7871 → toBase(7871, 2) — vượt xa trần 255 của decimal_to_binary", () => {
    const { rows } = runCharacterEncoding(parse(spec({
      text: PRECOMPOSED, encoding: "unicode_codepoint",
    })));
    expect(rows[0].decimal).toBe(7871);
    expect(rows[0].binary).toBe(toBase(7871, 2));
    expect(rows[0].decimal).toBeGreaterThan(255);
  });

  it("quy ước hiển thị lấy từ base_conversion, engine KHÔNG tự đệm số 0", () => {
    const { rows } = runCharacterEncoding(parse(spec({ text: "A" })));
    expect(rows[0].binary.startsWith("0")).toBe(false);
    expect(rows[0].binary).toBe(toBase(65, 2));
  });
});

/* ══════════ progressive reveal ══════════ */

describe("bảng hiện DẦN, không lộ kết quả cuối", () => {
  it("ENC-2: 'Tin' xử lý đúng thứ tự T, i, n", () => {
    const { rows } = runCharacterEncoding(parse(spec({ text: "Tin" })));
    expect(rows.map((r) => r.char)).toEqual(["T", "i", "n"]);
  });

  it("bước đầu chưa chốt hàng nào", () => {
    const st = stateOf(spec({ text: "Tin" }), 0);
    expect(committedRowCount(st)).toBe(0);
  });

  it("bước đầu KHÔNG lộ mã/nhị phân của ký tự sau", () => {
    const html = workspace(stateOf(spec({ text: "Tin" }), 0));
    expect(html).not.toContain(String(toBase("i".codePointAt(0) as number, 2)));
    expect(html).not.toContain("Đã mã hoá");
  });

  it("bước cuối mới hiện kết luận và đủ ba hàng", () => {
    const st = stateOf(spec({ text: "Tin" }));
    const last = { ...st, cursor: st.trace.steps.length - 1 };
    expect(committedRowCount(last)).toBe(3);
    expect(workspace(last)).toContain("Đã mã hoá");
  });

  it("mã chỉ xuất hiện SAU bước tra, nhị phân SAU bước đổi", () => {
    const st = stateOf(spec({ text: "A" }));
    expect(workspace({ ...st, cursor: 0 })).not.toContain("65");        // mới chọn ký tự
    expect(workspace({ ...st, cursor: 1 })).toContain("65");            // đã tra mã
    expect(workspace({ ...st, cursor: 1 })).not.toContain(toBase(65, 2));
    expect(workspace({ ...st, cursor: 2 })).toContain(toBase(65, 2));   // đã đổi
  });
});

/* ══════════ renderer chỉ đọc trace ══════════ */

describe("renderer không tự tính", () => {
  it("hiện đúng giá trị ENGINE PHÁT RA, kể cả khi trái trực giác", () => {
    // Bịa hàng nói 'A' có mã 999. Nếu renderer tự gọi codePointAt/toString(2)
    // nó sẽ hiện 65 và test này đỏ — đó là mục đích.
    const st = stateOf(spec({ text: "A" }));
    const forged: CharEncodingState = {
      ...st,
      cursor: st.trace.steps.length - 1,
      rows: [{ index: 0, char: "A", label: "A", codePoint: 999, decimal: 999, binary: "1111100111" }],
    };
    const html = workspace(forged);
    expect(html).toContain("999");
    expect(html).toContain("1111100111");
  });

  it("ký tự khoảng trắng có nhãn học sinh đọc được", () => {
    const { rows } = runCharacterEncoding(parse(spec({ text: " " })));
    expect(rows[0].label).toBe("dấu cách");
    expect(rows[0].decimal).toBe(32);
  });
});

/* ══════════ hợp đồng module ══════════ */

describe("module hợp đồng", () => {
  const mod = makeCharEncodingModule();

  it("khai đúng id, domain binary, 2D-only, có timeline", () => {
    expect(mod.id).toBe("binary.character_encoding");
    expect(mod.domain).toBe("binary");
    expect(mod.supportedVisualModes).toEqual(["2d"]);
    expect(mod.supportedVisualModes).not.toContain("3d");
    expect(mod.timeline).toBeTruthy();
  });

  it("validateConfig từ chối emoji (mở lại từ lịch sử cũng an toàn)", () => {
    expect(mod.validateConfig(spec({ text: EMOJI, encoding: "unicode_codepoint" })).ok).toBe(false);
  });

  it("init chạy engine, timeline khớp số bước", () => {
    const st = mod.init(parse(spec({ text: "Tin" })));
    expect(mod.timeline!.stepCount(st)).toBe(st.trace.steps.length);
    expect(st.rows).toHaveLength(3);
  });

  it("inspector hiện ký tự đang xét", () => {
    const st = stateOf(spec({ text: "A" }), 2);
    const html = renderToString(
      <CharEncodingInspector state={st} config={st.spec} busy={false} dispatch={noop} />,
    );
    expect(html).toContain("65");
  });
});
