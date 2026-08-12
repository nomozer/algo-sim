import { describe, expect, it } from "vitest";
import { registerAllSimulations } from "../../index";
import { getSimulation, listSimulations } from "../../registry";
import { offlineCatalog } from "../../../data/offline-catalog";
import { CONDITION_OPS, thresholdRange, withConditionParam } from "./condition-param";
import type { AlgorithmConfig, AlgorithmSimState } from "./model";

/**
 * W4B-4D — MIỀN CỦA ĐIỀU KIỆN LÀ MIỀN ĐÓNG, VÀ TỪ CHỐI KHÁC VỚI KẸP.
 *
 * ─── LỖ DO TIÊM LỖI BẮT ĐƯỢC, KHÔNG PHẢI PHÒNG XA ─────────────────────────
 *
 * Fault F8: đổi `withConditionParam` từ TỪ CHỐI ngưỡng ngoài khoảng sang KẸP về
 * biên — toàn bộ suite 1276 test vẫn XANH. Nghĩa là luật "từ chối, không kẹp"
 * (đã ghi thành comment trong `condition-param.ts` và là luật chung của mọi
 * miền trong repo — cùng chữ với `applyStyleChange` bên web) chưa từng được
 * kiểm. Kẹp im lặng nói dối hai lần: người gọi tưởng đã đặt được giá trị đó,
 * và học sinh thấy một con số mình không hề chọn.
 *
 * File này khoá đúng biên đó. Nó nói về MIỀN — còn chuyện "đổi ngưỡng thì kết
 * quả đổi" đã khoá ở `explore-ownership-w4b3a.test.ts`, không lặp lại ở đây.
 */

function countIfConfig(): AlgorithmConfig {
  if (listSimulations().length === 0) registerAllSimulations();
  const e = offlineCatalog().find((x) => x.simId === "algorithm.count_if")!;
  const mod = getSimulation("algorithm.count_if")!;
  const r = mod.validateConfig((e.envelope as { config: unknown }).config);
  if (!r.ok) throw new Error(r.error);
  return r.config as AlgorithmConfig;
}

describe("W4B-4D · ngưỡng ngoài khoảng bị TỪ CHỐI, không bị kẹp", () => {
  it("trên trần / dưới sàn ⇒ null — không có config nào mang giá trị bị kẹp", () => {
    const cfg = countIfConfig();
    const r = thresholdRange(cfg.data.array)!;
    for (const bad of [r.max + 1, r.max + 100, r.min - 1, r.min - 100]) {
      const out = withConditionParam(cfg, "condition.value", bad);
      expect(out, `ngưỡng ${bad} phải bị từ chối`).toBeNull();
    }
    /* Đối chứng — hai biên là giá trị HỢP LỆ, để phép đo trên không xanh nhờ
       một hàm từ chối tất. (Biên có thể trùng giá trị hiện tại ⇒ null hợp lệ
       theo luật "không đổi thì không state mới", nên thử biên KHÁC hiện tại.) */
    const other = cfg.data.condition!.value === r.max ? r.min : r.max;
    expect(withConditionParam(cfg, "condition.value", other)).not.toBeNull();
  });

  it("không phải số nguyên ⇒ null (không làm tròn hộ)", () => {
    const cfg = countIfConfig();
    for (const bad of [7.5, NaN, Infinity, "7.5", "bảy", true]) {
      expect(withConditionParam(cfg, "condition.value", bad as never), String(bad)).toBeNull();
    }
  });

  it("toán tử ngoài bảng ⇒ null; mọi toán tử TRONG bảng đều nhận", () => {
    const cfg = countIfConfig();
    for (const bad of ["===", "=>", "in", "LIKE", ""]) {
      expect(withConditionParam(cfg, "condition.op", bad), bad).toBeNull();
    }
    for (const op of CONDITION_OPS) {
      if (op === cfg.data.condition!.op) continue; // trùng hiện tại ⇒ null hợp lệ
      expect(withConditionParam(cfg, "condition.op", op), op).not.toBeNull();
    }
  });

  it("qua `apply`: action ngoài miền ⇒ state GIỮ NGUYÊN THAM CHIẾU", () => {
    /* Biên phải giữ ở cả tầng module, vì UI phát action qua đường này — thanh
       trượt vốn không ra ngoài miền, nhưng miền không được TIN thanh trượt. */
    const mod = getSimulation("algorithm.count_if")!;
    const cfg = countIfConfig();
    const s0 = mod.init(cfg) as AlgorithmSimState;
    const r = thresholdRange(cfg.data.array)!;
    for (const a of [
      { type: "set_param", name: "condition.value", value: r.max + 3 } as const,
      { type: "set_param", name: "condition.value", value: 7.5 } as const,
      { type: "set_param", name: "condition.op", value: "LIKE" } as const,
      { type: "set_param", name: "data.array", value: 1 } as const,
    ]) {
      expect(mod.apply(s0, a), JSON.stringify(a)).toBe(s0);
    }
  });
});
