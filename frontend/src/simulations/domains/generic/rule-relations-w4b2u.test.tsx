import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { renderToString } from "react-dom/server";
import { makeGenericModule } from "./index";
import { GenericWorkspace } from "./ui";
import { GENERIC_AND_SPEC, GENERIC_BINARY_SPEC } from "../../../data/sim-samples";

/**
 * W4B-2U §12 — QUAN HỆ PHẢI Ở TRÊN SÂN KHẤU, VÀ PHẢI ĐẾN TỪ DỮ LIỆU ĐÃ VALIDATE.
 *
 * Kết luận điều tra hợp đồng: DSL **đã đủ thông tin**. `rules[]` khai
 * `inputs → target` cùng toán tử (`op`), và engine dùng đúng dữ liệu đó để
 * TÍNH. Thứ thiếu chỉ là sân khấu không vẽ nó — quan hệ trước nay chỉ hiện dưới
 * dạng CHỮ ở mục "QUY TẮC" của Giải thích.
 *
 * Nên bất biến ở đây có HAI vế, và vế thứ hai mới là vế khó:
 *   1. spec CÓ khai rule ⇒ sân khấu phải vẽ quan hệ;
 *   2. spec KHÔNG khai ⇒ sân khấu KHÔNG được tự bịa ra đường nào.
 */

function build(spec: object) {
  const mod = makeGenericModule();
  const r = mod.validateConfig(spec);
  if (!r.ok) throw new Error(r.error);
  return { mod, config: r.config, state: mod.init(r.config) };
}

const html = (spec: object) => {
  const b = build(spec);
  return renderToString(
    <GenericWorkspace config={b.config} state={b.state} busy={false} dispatch={() => {}} />,
  );
};

/** Số đường quan hệ nét đứt (khác `edge` — edge vẽ nét liền). */
const relationLines = (h: string) => (h.match(/stroke-dasharray="4 5"/g) ?? []).length;

describe("W4B-2U · quan hệ do `rules` khai được VẼ trên sân khấu", () => {
  it("AND: hai đầu vào nối tới đầu ra, và toán tử đọc được", () => {
    const h = html(GENERIC_AND_SPEC);
    // rule: inputs [a,b] → target y ⇒ đúng hai đường.
    expect(relationLines(h), "cảnh AND vẫn là ba widget rời").toBe(2);
    expect(h, "không nói quan hệ LÀ GÌ").toContain(">AND<");
  });

  it("weighted_sum: mỗi bit nối tới ô kết quả", () => {
    const h = html(GENERIC_BINARY_SPEC);
    const inputs = GENERIC_BINARY_SPEC.rules[0].inputs.length;
    expect(relationLines(h)).toBe(inputs);
    expect(h).toContain(">Σ<");
  });

  it("quan hệ mang TÊN ĐỌC ĐƯỢC cho công nghệ hỗ trợ (không chỉ là nét vẽ)", () => {
    const h = html(GENERIC_AND_SPEC);
    expect(h).toMatch(/<title>A → Đầu ra<\/title>/);
    expect(h).toMatch(/<title>B → Đầu ra<\/title>/);
  });
});

describe("W4B-2U · renderer KHÔNG bịa quan hệ", () => {
  it("spec KHÔNG có rule ⇒ KHÔNG đường quan hệ nào", () => {
    /* Đây là vế chống-bịa. Một renderer "cứ nối các object lại cho đẹp" sẽ đỏ
       ở đây, và đó đúng là thứ `SIMULATION_VS_ILLUSTRATION_CONTRACT` cấm. */
    const noRules = { ...GENERIC_AND_SPEC, rules: [], interactions: [] };
    expect(relationLines(html(noRules))).toBe(0);
  });

  it("số đường = đúng số cặp (input, target) mà spec khai — không hơn", () => {
    for (const spec of [GENERIC_AND_SPEC, GENERIC_BINARY_SPEC]) {
      const declared = spec.rules.reduce((n, r) => n + (r.inputs?.length ?? 0), 0);
      expect(relationLines(html(spec)), `${spec.title}`).toBe(declared);
    }
  });

  it("nguồn quan hệ là `rules`, KHÔNG phải tiêu đề/nhãn/ngữ cảnh", () => {
    const src = readFileSync(new URL("./ui.tsx", import.meta.url), "utf-8")
      .replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");
    /* Cắt lát BẰNG MÃ, không bằng chú thích: `src` đã bị bóc chú thích ở trên
       nên mốc kết thúc dạng comment sẽ trả -1 và lát ăn tới cuối file (đúng lỗi
       đã dính: test đỏ vì `spec.title` ở một khối khác hẳn). */
    const start = src.indexOf("spec.rules.flatMap");
    const end = src.indexOf('o.type === "edge"', start);
    expect(start, "không tìm thấy khối quan hệ").toBeGreaterThan(0);
    expect(end, "không tìm thấy mốc kết thúc").toBeGreaterThan(start);
    const pass = src.slice(start, end);
    expect(pass).toContain("r.inputs");
    expect(pass).toContain("r.target");
    /* `<title>` trong khối này là TÊN KHẢ TRUY CẬP của đường quan hệ — hợp lệ,
       và cấm chuỗi "title" trần sẽ cấm nhầm chính nó. Thứ phải cấm là đọc
       TRƯỜNG NGỮ CẢNH của đề bài để quyết định vẽ gì. */
    for (const forbidden of ["spec.title", "summary", "description", ".includes(", "op === "]) {
      expect(pass, `quan hệ suy từ ngữ cảnh (${forbidden})`).not.toContain(forbidden);
    }
  });

  it("quan hệ TÍNH TOÁN phân biệt được với `edge` CÓ THẬT trong mô hình", () => {
    /* Hai thứ khác loại: `edge` là đối tượng của mô hình (dây, đoạn thẳng),
       quan hệ rule là phụ thuộc tính toán. Trông giống nhau là dạy sai. */
    const h = html(GENERIC_AND_SPEC);
    expect(h).toContain('stroke-dasharray="4 5"'); // quan hệ rule: nét đứt
    expect(relationLines(h)).toBeGreaterThan(0);
  });
});
