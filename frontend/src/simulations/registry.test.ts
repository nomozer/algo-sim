import { beforeEach, describe, expect, it } from "vitest";
import { registerSemanticDomain } from "./domains/semantic";
import { clearRegistryForTest, getSimulation, listSimulations, registerSimulation } from "./registry";

/**
 * Test tầng REGISTRY — sở hữu id, chống trùng, tra cứu, hợp đồng UI.
 *
 * ─── CHUYỂN FIXTURE SANG HÌNH HỌC (FRONTEND_LEGACY_FIXTURE_CUTOVER) ───────
 *
 * Bản trước dựng mọi ca bằng `makeAlgorithmModule` và khẳng định *"đăng ký đủ
 * 11 mô phỏng domain algorithm"*. Đó là fixture, không phải bất biến: thứ file
 * này sở hữu là **hành vi của registry**, và hành vi ấy không biết môn nào.
 *
 * Ba khối cũ đã được XOÁ chứ không chuyển, vì chủ thể của chúng là engine Tin
 * học chứ không phải registry — phân loại `LEGACY_SUBJECT_ASSERTION`:
 *
 *   · `mapper legacy algorithm_id → simulation_id` — `toSimulationId`/
 *     `fromLegacyAnalysis` ánh xạ 8 bài mẫu Tin học cũ. Không bài mẫu nào còn
 *     tồn tại, nên nó ánh xạ từ rỗng sang rỗng.
 *   · `validateConfig` — kiểm luật config của module algorithm (mảng quá dài,
 *     thiếu `target`, `binary_search` đòi dãy đã sắp). Luật của một môn đã gỡ.
 *   · `timeline capability + apply` và `getExplainContext` — kiểm engine
 *     algorithm (what-if swap, nhánh, exit_branch). Engine ấy đã gỡ.
 *
 * Bốn phép kiểm còn lại giữ NGUYÊN ý nghĩa, chỉ đổi module đem ra thử.
 */

beforeEach(() => {
  clearRegistryForTest();
});

describe("registry", () => {
  it("đăng ký domain hình học ⇒ registry có đúng module của nó", () => {
    registerSemanticDomain();
    const metas = listSimulations();
    expect(metas).toHaveLength(1);
    expect(metas[0].id).toBe("generic.semantic_program");
    // `interactionMode`/`hasTimeline` là hợp đồng của registry với shell, không
    // phải chi tiết của một môn: shell đọc chúng để quyết bày thanh bước.
    expect(metas.every((m) => m.interactionMode === "progressive")).toBe(true);
    expect(metas.every((m) => m.hasTimeline)).toBe(true);
  });

  it("từ chối id trùng và id sai định dạng", () => {
    registerSemanticDomain();
    const mod = getSimulation("generic.semantic_program")!;
    expect(() => registerSimulation(mod)).toThrow(/đã được đăng ký/);
    expect(() =>
      registerSimulation({ ...mod, id: "SaiDinhDang" }),
    ).toThrow(/dạng/);
  });

  it("getSimulation trả về module đúng id, undefined khi không có", () => {
    registerSemanticDomain();
    expect(getSimulation("generic.semantic_program")?.title).toBe(
      "Mô phỏng theo chương trình ngữ nghĩa",
    );
    // Một id ĐÚNG DẠNG nhưng chưa đăng ký phải trả `undefined`, không ném —
    // đó là điều kiện để `store.loadEnvelope` từ chối có địa chỉ thay vì crash.
    expect(getSimulation("khong.co.that")).toBeUndefined();
  });

  it("mọi module đăng ký phải có Workspace (hợp đồng UI của M2)", () => {
    registerSemanticDomain();
    for (const meta of listSimulations()) {
      const mod = getSimulation(meta.id)!;
      expect(mod.Workspace, `module ${meta.id} thiếu Workspace`).toBeDefined();
    }
  });
});
