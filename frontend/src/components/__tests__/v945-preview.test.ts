import { describe, expect, it } from "vitest";
import { isClearlyInvalidPdf, validateComposerFile } from "../../llm/input";

describe("PDF preview check", () => {
  it("identifies an obviously truncated PDF and a non-PDF signature", async () => {
    expect(await isClearlyInvalidPdf(new File(["%PDF-1.4\n%%EOF"], "de.pdf", { type: "application/pdf" }))).toBe(true);
    expect(await isClearlyInvalidPdf(new File(["not a PDF".repeat(10)], "de.pdf", { type: "application/pdf" }))).toBe(true);
  });
  it("does not claim to validate a longer file with a PDF signature", async () => {
    expect(await isClearlyInvalidPdf(new File(["%PDF-1.7\n", "x".repeat(100)], "de.pdf", { type: "application/pdf" }))).toBe(false);
  });
  it("rejects a truncated PDF before it can be submitted", () => {
    expect(validateComposerFile({ name: "de.pdf", type: "application/pdf", size: 14 }).ok).toBe(false);
  });
});
