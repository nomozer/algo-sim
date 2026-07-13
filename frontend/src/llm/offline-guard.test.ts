import { describe, expect, it } from "vitest";
import { analyzeViaServer, editViaServer } from "./client";
import { BLOCK_MESSAGE } from "../test-setup";

/**
 * Canary (M7.14T): chứng minh guard offline của vitest thật sự nổ. Nếu ai đó
 * gỡ setupFiles, các test này đỏ ngay — thay vì âm thầm gọi mạng thật.
 */

describe("offline guard — vitest không gọi mạng", () => {
  it("analyzeViaServer bị chặn ở fetch", async () => {
    await expect(
      analyzeViaServer({ type: "text", content: "Tìm max dãy 3 1 2" }),
    ).rejects.toThrow(); // client bọc lỗi mạng thành thông điệp hướng dẫn
  });

  it("editViaServer bị chặn ở fetch", async () => {
    await expect(
      editViaServer({ simulationId: "generic.rule_scene", config: {}, instruction: "Thêm D." }),
    ).rejects.toThrow();
  });

  it("fetch thô ném đúng thông điệp guard", async () => {
    await expect(fetch("/api/health")).rejects.toThrow(BLOCK_MESSAGE);
  });
});
