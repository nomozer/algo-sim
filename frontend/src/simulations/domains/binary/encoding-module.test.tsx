import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";

import { toBase } from "./convert-module";
import {
  CharEncodingInspector,
  CharEncodingWorkspace,
  codePointsOf,
  committedRowCount,
  divisionsSoFar,
  displayChar,
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
  return { spec: s, trace: run.trace, cursor, rows: run.rows, meta: run.meta };
}

/** Cursor của bước đầu tiên có phase cho trước — thay cho số học cursor. */
function at(st: CharEncodingState, phase: string, charIndex = 0): number {
  const i = st.meta.findIndex((m) => m.phase === phase && m.charIndex === charIndex);
  if (i < 0) throw new Error(`không có phase ${phase} cho ký tự ${charIndex}`);
  return i;
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

  it("mã chỉ xuất hiện SAU bước tra, nhị phân SAU khi ĐỌC NGƯỢC số dư", () => {
    const st = stateOf(spec({ text: "A" }));
    expect(workspace({ ...st, cursor: at(st, "select_character") })).not.toContain("65");
    expect(workspace({ ...st, cursor: at(st, "map_to_code") })).toContain("65");
    // đã tra mã nhưng CHƯA chia — không được lộ dãy bit
    expect(workspace({ ...st, cursor: at(st, "map_to_code") })).not.toContain(toBase(65, 2));
    // đã mở cơ chế nhưng chưa chạy hết — vẫn chưa có dãy bit
    expect(workspace({ ...st, cursor: at(st, "begin_conversion") })).not.toContain(toBase(65, 2));
    expect(workspace({ ...st, cursor: at(st, "read_remainders") })).toContain(toBase(65, 2));
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

describe("W3-VR — lỗi chỉ review ảnh mới thấy", () => {
  it("VR1: bước cuối KHÔNG lặp thuyết minh trùng băng kết quả", () => {
    const st = stateOf(spec({ text: "A" }));
    const html = workspace({ ...st, cursor: st.trace.steps.length - 1 });
    const marker = "Đã mã hoá 1 ký tự";
    const hits = html.split(marker).length - 1;
    expect(hits).toBe(1);
  });

  it("VR2: ký tự '7' hiện có dấu nháy — không lẫn với SỐ 7", () => {
    const st = stateOf(spec({ text: "7" }));
    const html = workspace({ ...st, cursor: st.trace.steps.length - 1 });
    expect(html).toContain("&#x27;7&#x27;");   // '7' đã escape trong SSR
    const { rows } = runCharacterEncoding(parse(spec({ text: "7" })));
    expect(displayChar(rows[0])).toBe("'7'");
    expect(rows[0].decimal).toBe(55);
  });

  it("VR2: ký tự có nhãn mô tả KHÔNG bị bọc nháy", () => {
    const { rows } = runCharacterEncoding(parse(spec({ text: " " })));
    expect(displayChar(rows[0])).toBe("dấu cách");
  });
});

/* ══════════ M17 P1a — W3-SIM: CƠ CHẾ THẬT, không phải công bố ══════════ */

describe("A. reuse — không có bộ chuyển đổi thứ hai", () => {
  it("cơ chế chia lấy dư đến TỪ base_conversion, không phải bản sao", async () => {
    const shared = await import("./base-conversion");
    const conv = await import("./convert-module");
    // convert-module re-export CHÍNH hàm của module thuần (cùng tham chiếu)
    expect(conv.divideSteps).toBe(shared.divideSteps);
    expect(conv.toBase).toBe(shared.toBase);
  });

  it("encoding-module KHÔNG tự cài phép chia/lấy dư", () => {
    const src = readFileSync(new URL("./encoding-module.tsx", import.meta.url), "utf-8");
    // Chỉ xét THÂN engine, và bỏ chú thích: header của file có nhắc `toBase()`
    // để giải thích vì sao nó không còn là nguồn runtime — nhắc trong chú thích
    // không phải là gọi.
    const body = src
      .slice(src.indexOf("export function runCharacterEncoding"),
             src.indexOf("export function metaAt"))
      .replace(/\/\*[\s\S]*?\*\//g, "")
      .replace(/\/\/.*$/gm, "");
    expect(body).toContain("divideSteps(");
    expect(body).not.toContain("toBase(");        // không còn nguồn kết quả thứ hai
    expect(body).not.toMatch(/%\s*2\b/);          // không tự lấy dư
    expect(body).not.toContain("toString(2)");
  });

  it("chỉ có MỘT nơi cài divideSteps trong toàn thư mục binary", () => {
    const dir = new URL("./", import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1");
    const owners = readdirSync(dir)
      .filter((f) => /\.tsx?$/.test(f) && !/\.test\./.test(f))
      .filter((f) => /function divideSteps/.test(readFileSync(join(dir, f), "utf-8")));
    expect(owners).toEqual(["base-conversion.ts"]);
  });
});

describe("B. cơ chế THẬT — chia tới thương 0", () => {
  it("'A' sinh chuỗi chia thật từ 65 xuống thương 0", () => {
    const st = stateOf(spec({ text: "A" }));
    const divs = st.meta.filter((m) => m.division).map((m) => m.division!);
    expect(divs.length).toBeGreaterThan(1);
    expect(divs[0].value).toBe(65);
    expect(divs[divs.length - 1].quotient).toBe(0);
  });

  it("mỗi bước có thương/số dư ĐÚNG và nối tiếp bước trước", () => {
    const st = stateOf(spec({ text: "A" }));
    const divs = st.meta.filter((m) => m.division).map((m) => m.division!);
    divs.forEach((d, k) => {
      expect(d.base).toBe(2);
      expect(d.quotient).toBe(Math.floor(d.value / 2));
      expect(d.remainder).toBe(d.value % 2);
      expect(d.digit).toBe(String(d.remainder));
      if (k > 0) expect(d.value).toBe(divs[k - 1].quotient);   // nối tiếp thật
      expect(d.collected.length).toBe(k + 1);                  // thu dần, không lộ trước
    });
  });

  it("số dư đọc NGƯỢC sinh đúng dãy nhị phân", () => {
    for (const text of ["A", "7", " "]) {
      const st = stateOf(spec({ text }));
      const divs = st.meta.filter((m) => m.division).map((m) => m.division!);
      const derived = divs.map((d) => d.digit).reverse().join("");
      expect(derived).toBe(st.rows[0].binary);
    }
  });

  it("kết quả KHÔNG lấy từ trường tiền tính trong spec", () => {
    expect(validateCharEncodingSpec({ ...(spec() as object), binary_values: ["1000001"] }).ok).toBe(false);
    const st = stateOf(spec({ text: "A" }));
    expect(Object.keys(st.spec)).toEqual(expect.not.arrayContaining(["rows", "binary_values"]));
  });

  it("bước đầu KHÔNG chứa dãy nhị phân cuối", () => {
    const st = stateOf(spec({ text: "A" }), 0);
    expect(workspace(st)).not.toContain(toBase(65, 2));
    expect(st.meta[0].division).toBeUndefined();
  });

  it("chuyển trạng thái VƯỢT QUÁ ẩn→hiện: số bị chia thật sự giảm", () => {
    const st = stateOf(spec({ text: "A" }));
    const values = st.meta.filter((m) => m.division).map((m) => m.division!.value);
    expect(values).toEqual([...values].sort((a, b) => b - a));
    expect(new Set(values).size).toBe(values.length);        // không dậm chân
  });
});

describe("C. Unicode BMP đi qua cùng cơ chế", () => {
  it("'ế' = 7871 và chia được dù vượt xa trần 255 của decimal_to_binary", () => {
    const st = stateOf(spec({ text: PRECOMPOSED, encoding: "unicode_codepoint" }));
    expect(st.rows[0].decimal).toBe(7871);
    const divs = st.meta.filter((m) => m.division).map((m) => m.division!);
    expect(divs[0].value).toBe(7871);
    expect(divs.some((d) => d.value > 255)).toBe(true);
    expect(divs.map((d) => d.digit).reverse().join("")).toBe(toBase(7871, 2));
  });

  it("emoji/surrogate vẫn bị từ chối y như trước", () => {
    expect(validateCharEncodingSpec(spec({ text: EMOJI, encoding: "unicode_codepoint" })).ok).toBe(false);
    expect(validateCharEncodingSpec(spec({ text: LONE_SURROGATE, encoding: "unicode_codepoint" })).ok).toBe(false);
  });

  it("decomposed vẫn KHÔNG bị gộp — normalization không đổi", () => {
    const st = stateOf(spec({ text: DECOMPOSED, encoding: "unicode_codepoint" }));
    expect(st.rows).toHaveLength(3);
    expect(st.rows.map((r) => r.codePoint)).toEqual([0x0065, 0x0302, 0x0301]);
  });
});

describe("D. chính sách rút gọn nhiều ký tự — trung thực", () => {
  it("ký tự ĐẦU bung chi tiết, ký tự sau rút gọn", () => {
    const st = stateOf(spec({ text: "Tin" }));
    expect(st.meta.some((m) => m.charIndex === 0 && m.phase === "divide_step")).toBe(true);
    for (const i of [1, 2]) {
      expect(st.meta.some((m) => m.charIndex === i && m.phase === "divide_step")).toBe(false);
      expect(st.meta.some((m) => m.charIndex === i && m.phase === "convert_compact")).toBe(true);
    }
  });

  it("KHÔNG lệch kết quả giữa đường chi tiết và đường rút gọn", () => {
    const st = stateOf(spec({ text: "Tin" }));
    for (const row of st.rows) expect(row.binary).toBe(toBase(row.decimal, 2));
    // và ký tự rút gọn cho đúng cái mà đường chi tiết sẽ cho
    const solo = stateOf(spec({ text: "i" }));
    expect(st.rows[1].binary).toBe(solo.rows[0].binary);
  });

  it("bước rút gọn NÓI RÕ là cùng quy tắc, không giả vờ đã chia từng bước", () => {
    const st = stateOf(spec({ text: "Tin" }));
    const i = st.meta.findIndex((m) => m.phase === "convert_compact");
    expect(st.trace.steps[i].narration).toContain("CÙNG quy tắc chia lấy dư");
  });

  it("timeline không phình vô lý với 12 code point", () => {
    const st = stateOf(spec({ text: "abcdefghijkl" }));
    expect(st.rows).toHaveLength(12);
    expect(st.trace.steps.length).toBeLessThan(60);
  });
});

describe("E. renderer chỉ đọc trace — không tự chia", () => {
  it("trace BỊA về phép chia được hiện nguyên xi", () => {
    const st = stateOf(spec({ text: "A" }));
    const cur = at(st, "divide_step");
    const forged: CharEncodingState = {
      ...st,
      cursor: cur,
      meta: st.meta.map((m, k) => k === cur
        ? { ...m, division: { value: 65, base: 2, quotient: 30, remainder: 5,
                              digit: "5", stepIndex: 0, collected: ["5"] } }
        : m),
    };
    // So Ô BẢNG, không so cả trang: thuyết minh vẫn là câu THẬT trong trace
    // (ta chỉ bịa `meta.division`), nên "32" xuất hiện ở băng thuyết minh là ĐÚNG.
    const html = workspace(forged);
    expect(html).toContain("<td>30</td>");        // thương BỊA hiện ở bảng
    expect(html).toContain("<td>5</td>");         // số dư BỊA hiện ở bảng
    expect(html).not.toContain("<td>32</td>");    // renderer KHÔNG tự tính thương thật
  });

  it("renderer không gọi utility đổi cơ số", () => {
    const src = readFileSync(new URL("./encoding-module.tsx", import.meta.url), "utf-8");
    const view = src.slice(src.indexOf("function DivisionPanel"));
    for (const banned of ["divideSteps(", "toBase(", "toString(2)", "codePointAt("]) {
      expect(view, `renderer gọi ${banned}`).not.toContain(banned);
    }
  });

  it("Previous/Next khôi phục đúng trạng thái chia", () => {
    const st = stateOf(spec({ text: "A" }));
    const cur = at(st, "divide_step");
    const forward = divisionsSoFar({ ...st, cursor: cur + 1 }, cur + 1);
    const back = divisionsSoFar({ ...st, cursor: cur }, cur);
    expect(forward.length).toBe(back.length + 1);
    // quay lại rồi tiến lại cho đúng y hệt (tất định, không tích luỹ)
    expect(divisionsSoFar({ ...st, cursor: cur + 1 }, cur + 1)).toEqual(forward);
  });

  it("bảng chia chỉ hiện khi cơ chế đang chạy", () => {
    const st = stateOf(spec({ text: "A" }));
    expect(workspace({ ...st, cursor: at(st, "select_character") })).not.toContain("Số bị chia");
    expect(workspace({ ...st, cursor: at(st, "divide_step") })).toContain("Số bị chia");
    expect(workspace({ ...st, cursor: st.trace.steps.length - 1 })).not.toContain("Số bị chia");
  });

  it("không lộ token kỹ thuật ra màn hình", () => {
    const st = stateOf(spec({ text: "A" }));
    for (let c = 0; c < st.trace.steps.length; c++) {
      const html = workspace({ ...st, cursor: c });
      for (const t of ["divide_step", "read_remainders", "convert_compact", "charIndex",
                       "CharEncodingSpec", "binary.character_encoding", "undefined", "NaN"]) {
        expect(html, `lo token ${t}`).not.toContain(t);
      }
    }
  });
});

describe("W3-SIM-VR — lỗi chỉ review ảnh mới thấy", () => {
  it("VR1: bước đọc ngược KHÔNG lặp kết luận của băng thuyết minh", () => {
    const st = stateOf(spec({ text: "A" }));
    const html = workspace({ ...st, cursor: at(st, "read_remainders") });
    const ket = "nhị phân là 1000001";
    expect(html.split(ket).length - 1).toBeLessThanOrEqual(1);
  });

  it("VR1: vẫn ĐỐI CHIẾU được hai chiều đọc", () => {
    const st = stateOf(spec({ text: "T" }));   // 84 → 1010100, KHÔNG đối xứng
    const html = workspace({ ...st, cursor: at(st, "read_remainders") });
    expect(html).toContain("từ trên xuống");
    expect(html).toContain("từ DƯỚI LÊN");
    expect(html).toContain("0 0 1 0 1 0 1");   // thứ tự sinh
    expect(html).toContain("1 0 1 0 1 0 0");   // đọc ngược = 1010100
  });
});
