import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { registerAllSimulations } from "./index";
import { listSimulations } from "./registry";

/**
 * W13 — KHÔNG BỀ MẶT HỌC SINH NÀO PHÁT NGÔN ĐÚNG/SAI.
 *
 * ─── VÌ SAO FILE NÀY TỒN TẠI ───────────────────────────────────────────────
 *
 * `simulations/types.ts` khai: *"Không bề mặt học sinh nào còn phát ngôn
 * đúng/sai — khoá bởi `no-verdict.test.ts`"*. Nhưng tới 2026-08-21 file đó
 * **chưa từng được viết**: W13 gỡ `PredictionCapability` khỏi production rồi
 * dừng ở đó, để lại 26 file test gọi API đã chết và bất biến này **không có ai
 * canh**. Một tài liệu khai có guard mà guard không tồn tại còn tệ hơn không
 * khai — nó làm người sau tin là đã được bảo vệ.
 *
 * Đây là bản trả nợ. Nó KHÔNG khôi phục `predict`/`challengeOpen`; nó khoá
 * đúng thứ còn ý nghĩa sau khi hai thứ kia bị gỡ.
 *
 * ─── RANH GIỚI ─────────────────────────────────────────────────────────────
 *
 * "Không phát ngôn đúng/sai" nói về **phán quyết trên thao tác của học sinh**.
 * Nó KHÔNG cấm engine phản hồi một thao tác ngoài phạm vi hợp lệ
 * (`InteractionFeedback` của miền generic — bất biến #11/#12): câu "không kéo
 * được cột vào vùng đã duyệt" là mô tả CƠ CHẾ, không phải chấm điểm.
 */

registerAllSimulations();

const SRC = join(__dirname, "..");

/** Năng lực đã bị gỡ — module nào khai lại là quay về hỏi-đáp có chấm điểm. */
const CAPABILITY_DA_GO = ["predict", "prediction", "submitPrediction"] as const;

describe("W13 §1 — không module nào khai lại năng lực chấm điểm", () => {
  it("không module nào còn khai `predict`", () => {
    const pham = listSimulations()
      .filter((m) => (m as unknown as Record<string, unknown>).predict !== undefined)
      .map((m) => m.id);
    expect(pham, `module khai lại năng lực đã gỡ:\n${pham.join("\n")}`).toEqual([]);
  });

  it("hợp đồng module KHÔNG khai lại `PredictionCapability`", () => {
    const types = readFileSync(join(SRC, "simulations/types.ts"), "utf-8");
    // Chỉ được nhắc trong khối chú thích giải thích vì sao đã gỡ.
    expect(types).not.toMatch(/^\s*predict\??:/m);
    expect(types).not.toMatch(/export interface PredictionCapability/);
  });
});

describe("W13 §2 — store không giữ trạng thái hỏi-đáp", () => {
  const store = readFileSync(join(SRC, "state/store.ts"), "utf-8");

  it.each(CAPABILITY_DA_GO)("`%s` không còn là trường của AppState", (ten) => {
    expect(store).not.toMatch(new RegExp(`^\\s*${ten}\\b\\s*[:?]`, "m"));
  });

  it("không còn cờ mở/đóng chế độ chấm điểm", () => {
    expect(store).not.toMatch(/^\s*challengeOpen\s*[:?]/m);
    expect(store).not.toMatch(/^\s*setChallengeOpen\s*[:?]/m);
  });
});

describe("W13 §3 — thành phần chở phán quyết đã bị gỡ khỏi kho mã", () => {
  it.each(["components/PredictionBar.tsx", "components/SearchActionZone.tsx"])(
    "%s không còn tồn tại",
    (rel) => {
      expect(() => readFileSync(join(SRC, rel), "utf-8")).toThrow();
    },
  );
});
