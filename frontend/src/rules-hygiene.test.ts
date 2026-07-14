import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

/**
 * M9-UX1 §12 — VỆ SINH RULES.md (tests 27–29).
 *
 * docs/RULES.md v0.3 mô tả kiến trúc KHÔNG còn đúng (ba nguồn trace, tầng code
 * Pyodide, vẽ tự do llm_script) — một coding agent tương lai đọc nó có thể xây
 * theo kiến trúc cũ. Khoá bằng test: RULES.md hiện hành phải là tài liệu con
 * trỏ ngắn (thứ tự đọc + luật cứng), nội dung cũ nằm ở docs/legacy có cảnh báo.
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

describe("docs/legacy/RULES_v0.3.md — bản cũ được bảo tồn kèm cảnh báo", () => {
  const legacy = readFileSync(join(DOCS, "legacy", "RULES_v0.3.md"), "utf-8");

  it("(28) mở đầu bằng cảnh báo LEGACY rõ ràng", () => {
    const head = legacy.slice(0, 500).toUpperCase();
    expect(head).toContain("LEGACY");
    expect(head).toContain("KHÔNG");
  });

  it("nội dung lịch sử còn nguyên (v0.3, ba lớp trace)", () => {
    expect(legacy).toContain("v0.3");
    expect(legacy).toContain("Pyodide");
  });
});
