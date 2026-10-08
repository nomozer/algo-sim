import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

/**
 * M9-UX1 §12 — VỆ SINH RULES.md (tests 27–29).
 *
 * docs/RULES.md v0.3 mô tả kiến trúc KHÔNG còn đúng (ba nguồn trace, tầng code
 * Pyodide, vẽ tự do llm_script) — một coding agent tương lai đọc nó có thể xây
 * theo kiến trúc cũ. Khoá bằng test: RULES.md hiện hành phải là tài liệu con
 * trỏ ngắn (thứ tự đọc + luật cứng). Bản v0.3 từng giữ ở docs/legacy kèm cảnh báo
 * (test 28) đã gỡ ở run `docs-cleanup` — hệ Tin học đã retire, không ai đọc nó; lấy
 * lại từ git history nếu cần tra.
 */

const DOCS = join(__dirname, "..", "..", "docs");

describe("docs/RULES.md — con trỏ hiện hành, không phải kiến trúc cũ", () => {
  const rules = readFileSync(join(DOCS, "RULES.md"), "utf-8");

  it("(27) không còn tuyên bố kiến trúc cũ (ba nguồn trace / Pyodide / llm_script)", () => {
    expect(rules).not.toContain("Pyodide");
    expect(rules).not.toContain("llm_script");
    expect(rules).not.toContain("ba nguồn trace");
    expect(rules).not.toContain("Vẽ tự do");
  });

  it("(29) nêu đúng thứ tự đọc + CODE/TESTS THẮNG", () => {
    for (const doc of [
      "ARCHITECTURE_MAP.md",
      "CURRENT_STATE.md",
      "CORRECTNESS.md",
      "COVERAGE.md",
      "CODE_INDEX.md",
    ]) {
      expect(rules).toContain(doc);
    }
    expect(rules.toUpperCase()).toContain("CODE/TESTS");
  });

  it("tóm tắt các luật cứng bền vững (LLM không sở hữu runtime; engine tất định; tương tác chạm cơ chế)", () => {
    expect(rules).toContain("LLM");
    expect(rules).toContain("tất định");
    expect(rules).toContain("cơ chế");
  });
});
