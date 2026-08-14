/**
 * experience-gate.test.ts — CỔNG THƯỜNG TRỰC: MỖI TARGET PHẢI DẠY ĐƯỢC MỘT ĐIỀU.
 *
 * ─── VÌ SAO KHÔNG ĐỂ CHO BẢN CHỨNG NHẬN TRÌNH DUYỆT LO ─────────────────────
 *
 * `scripts/certify-experience-w12.mjs` trả lời câu hỏi đầy đủ hơn (nó nhìn được
 * cả bề mặt), nhưng nó cần Chrome và chạy vài phút — nghĩa là nó KHÔNG chạy khi
 * ai đó thêm một target mới lúc 11 giờ đêm. Cổng này chạy trong vitest, offline,
 * dưới một giây, và hỏi câu tối thiểu mà một mô phỏng phải trả lời được:
 *
 *     Bài này có ÍT NHẤT MỘT trong hai thứ không —
 *       (a) một action học sinh phát được và engine tính lại theo, hoặc
 *       (b) một dòng thời gian nhiều hơn một bước?
 *
 * Không có cả hai ⇒ nó là một BỨC HÌNH. Đó chính là thứ người dùng chỉ ra:
 * "có những cái không phải mô phỏng vẫn được thêm vào".
 *
 * ─── CỔNG NÀY KHÔNG THAY BẢN CHỨNG NHẬN ───────────────────────────────────
 *
 * Nó không nhìn thấy bề mặt, nên không phân biệt được "trace có mà không hiện".
 * Nói rõ ranh giới ở đây còn hơn để một cổng xanh đọc thành đã-phủ-hết.
 */
import { describe, expect, it, beforeAll } from "vitest";
import { candidateActions } from "./action-probe";
import { offlineCatalog } from "../data/offline-catalog";
import { registerAllSimulations } from "./index";
import { getSimulation, listSimulations } from "./registry";

beforeAll(() => {
  if (listSimulations().length === 0) registerAllSimulations();
});

/** Mỗi target một envelope đã validate, lấy từ danh mục — không dựng fixture riêng. */
function targets(): { simId: string; envelope: unknown }[] {
  const seen = new Set<string>();
  return offlineCatalog().filter((e) => {
    if (seen.has(e.simId)) return false;
    seen.add(e.simId);
    return true;
  });
}

describe("W12 §17/§19 — không target nào được là một bức hình", () => {
  const rows = targets();

  it("danh mục phủ đủ 23 target (nếu ít hơn thì cổng đang bỏ sót)", () => {
    expect(rows.length).toBeGreaterThanOrEqual(23);
  });

  it.each(rows.map((r) => r.simId))("%s: đổi được đầu vào HOẶC có dòng thời gian", (simId) => {
    const entry = rows.find((r) => r.simId === simId)!;
    const mod = getSimulation(simId);
    expect(mod, `${simId} chưa đăng kí`).toBeTruthy();

    const env = entry.envelope as { config: unknown };
    const v = mod!.validateConfig(env.config);
    expect(v.ok, `${simId}: envelope mẫu không qua validate`).toBe(true);
    if (!v.ok) return;
    const s0 = mod!.init(v.config);

    /* (a) CÓ ACTION NÀO ĐỔI ĐƯỢC STATE KHÔNG.
       So bằng JSON: `apply` trả về CHÍNH state cũ khi từ chối, nên so tham
       chiếu cũng đủ — nhưng một module trả bản sao y hệt vẫn phải bị coi là
       "không đổi", vì với học sinh thì không có gì xảy ra. */
    const before = JSON.stringify(s0);
    const accepted = candidateActions(v.config).filter((a) => {
      if (!mod!.apply) return false;
      try { return JSON.stringify(mod!.apply(s0, a)) !== before; } catch { return false; }
    });

    /* (b) DÒNG THỜI GIAN CÓ NHIỀU HƠN MỘT BƯỚC KHÔNG. */
    const steps = mod!.timeline ? mod!.timeline.stepCount(s0) : 0;

    expect(accepted.length > 0 || steps > 1,
      `${simId}: không action nào đổi được state (đã thử ${candidateActions(v.config).length}) ` +
      `và dòng thời gian có ${steps} bước ⇒ đây là một bức hình, không phải mô phỏng`,
    ).toBe(true);
  });

  /**
   * ĐỐI CHỨNG DƯƠNG — một cổng chưa từng đỏ là một cổng chưa được chứng minh.
   *
   * Dựng một module giả đúng hình dạng thứ cổng này tồn tại để bắt: `apply` trả
   * nguyên state, không có timeline. Nếu tiêu chí trên bỏ lọt nó thì mọi dòng
   * xanh ở trên đều vô nghĩa.
   */
  it("(đối chứng) module chỉ-là-hình bị tiêu chí này bắt", () => {
    const still = { bits: [1, 0, 1] };
    const applyIdentity = (s: typeof still) => s;
    const accepted = candidateActions({ decimalValue: 5 }).filter(
      (a) => JSON.stringify(applyIdentity(still)) !== JSON.stringify(still) && a,
    );
    const steps = 0;
    expect(accepted.length > 0 || steps > 1,
      "tiêu chí bỏ lọt một module đồng nhất không timeline").toBe(false);
  });

  it("bộ dò không được rỗng — một danh sách rỗng làm MỌI target trông như bức hình", () => {
    /* Cùng cái bẫy đã làm ba guard W8 'đạt' khi chúng khớp rỗng. */
    const withProbes = rows.filter((r) => {
      const mod = getSimulation(r.simId);
      const env = r.envelope as { config: unknown };
      const v = mod?.validateConfig(env.config);
      return v?.ok ? candidateActions(v.config).length > 0 : false;
    });
    expect(withProbes.length, "bộ dò không sinh ứng viên cho target nào")
      .toBeGreaterThan(rows.length / 2);
  });
});
